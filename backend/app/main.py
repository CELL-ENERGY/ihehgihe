"""
Jan Nidhi Spotter Backend — Main Application

Citizen verification and proof submission API for monitoring public works.
Features:
- Mandatory 6-field citizen verification with photo & GPS
- Supabase Cloud Storage integration
- Deferred XP gamification (+150 XP upon explicit claim)
- Built-in interactive Web Portal for citizens and admins

Swagger UI: http://127.0.0.1:8001/docs
Web Portal: http://127.0.0.1:8001/
"""

import os
from dotenv import load_dotenv
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.verification import router as verification_router

# ---------------------------------------------------------------------------
# Create FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Jan Nidhi Spotter Backend",
    description=(
        "Citizen verification and proof submission platform for monitoring "
        "public works. Citizens submit ground photographic proof with GPS coordinates, "
        "and claim +150 XP to level up."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

cors_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if cors_origins_env:
    allowed_origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(verification_router)

# ---------------------------------------------------------------------------
# Mount Static Files: Built React Frontend (frontend/dist) & Legacy Static
# ---------------------------------------------------------------------------

# Resolve frontend/dist directory
possible_dist_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "dist")),
]

frontend_dist_dir = None
for candidate in possible_dist_dirs:
    if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "index.html")):
        frontend_dist_dir = candidate
        break

if frontend_dist_dir:
    assets_dir = os.path.join(frontend_dist_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ---------------------------------------------------------------------------
# Database table creation on startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """Create all database tables and seed default admin accounts on startup."""
    Base.metadata.create_all(bind=engine)

    from app.database.database import SessionLocal
    from app.models.verification import User
    from app.services.auth import hash_password

    db = SessionLocal()
    try:
        # Seed legacy admin account (username: admin, password: admin)
        admin_user = db.query(User).filter(
            (User.email == "admin") | (User.email == "admin@jannidhi.gov.in")
        ).first()
        if not admin_user:
            admin_user = User(
                email="admin",
                name="System Admin",
                hashed_password=hash_password("admin"),
                xp=0,
                level=1,
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            print("[SEED] Legacy admin seeded (username: admin / password: admin)")

        # Seed localhost dev admin account (email: admin@gg, password: admin)
        dev_admin = db.query(User).filter(User.email == "admin@gg").first()
        if not dev_admin:
            dev_admin = User(
                email="admin@gg",
                name="Dev Admin",
                hashed_password=hash_password("admin"),
                xp=0,
                level=1,
                is_admin=True,
            )
            db.add(dev_admin)
            db.commit()
            print("[SEED] Dev admin seeded (email: admin@gg / password: admin)")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health & Root endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
)
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Jan Nidhi Spotter"}


@app.get(
    "/",
    tags=["Health"],
    summary="Service root / Web Portal",
    description="Serves production React app or API status.",
)
def root(request: Request):
    """Serve React production app or fallback status."""
    if frontend_dist_dir:
        index_file = os.path.join(frontend_dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

    accept_header = request.headers.get("accept", "")
    legacy_index = os.path.join(static_dir, "index.html")
    if "text/html" in accept_header and os.path.exists(legacy_index):
        return FileResponse(legacy_index)

    return {
        "status": "online",
        "service": "Jan Nidhi Spotter Backend",
    }


# ---------------------------------------------------------------------------
# SPA Catch-all Route for React Router
# ---------------------------------------------------------------------------

@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    """Serve static files from frontend/dist or fallback to index.html for client-side routing."""
    if frontend_dist_dir:
        # Check if direct file exists (e.g. favicon.ico, vite.svg)
        potential_file = os.path.join(frontend_dist_dir, full_path)
        if os.path.isfile(potential_file):
            return FileResponse(potential_file)

        # Fallback to SPA index.html
        index_file = os.path.join(frontend_dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

    return {"detail": "Not Found"}
