# 🚀 Jan Nidhi Spotter — Online Deployment Guide (Unified Option B)

This project is configured as a **unified single-service full-stack web application**. The FastAPI backend automatically serves the production-built React frontend from `frontend/dist`. 

You get:
- **One single URL** for both frontend and backend (e.g. `https://jan-nidhi-spotter.onrender.com`).
- **Zero CORS issues** because both frontend and backend share the exact same origin.
- All API routes (`/auth`, `/verifications`, `/users`, `/admin`, `/docs`, `/health`) work directly alongside the React SPA.

---

## Required Environment Variables

When deploying to your hosting provider, configure these environment variables in the provider dashboard (copied from your `backend/.env`):

| Variable | Description | Example / Source |
|---|---|---|
| `DATABASE_URL` | Cloud PostgreSQL connection string | `postgresql://...supabase.co:5432/postgres` |
| `SUPABASE_URL` | Supabase Cloud project URL | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | Supabase service or anon key | `eyJhbGci...` |
| `JWT_SECRET` | Secret key for signing auth tokens | Any secure string (e.g. 32+ characters) |
| `PYTHON_VERSION` | Python runtime version | `3.11.9` |

---

## Option 1: Deploy on Render (Recommended & Free Tier Available)

Render automatically recognizes either `render.yaml` or standard Python web services.

### Method A: Connect Git Repository (Simplest)
1. Push your repository to **GitHub** or **GitLab**.
2. Go to [dashboard.render.com](https://dashboard.render.com) and click **New +** → **Web Service**.
3. Select your repository.
4. Fill in the settings:
   - **Name**: `jan-nidhi-spotter`
   - **Environment**: `Python`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
5. Under **Environment Variables**, add:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `JWT_SECRET`
   - `PYTHON_VERSION` = `3.11.9`
6. Click **Create Web Service**. Render will automatically build the React assets, install backend dependencies, and launch your live application with a free `https://*.onrender.com` SSL domain.

---

## Option 2: Deploy on Railway

Railway supports automatic Dockerfile or Procfile deployment.

1. Push your code to GitHub.
2. Go to [railway.com](https://railway.com) and click **New Project** → **Deploy from GitHub repo**.
3. Select your repository.
4. Railway will detect the included [Dockerfile](Dockerfile) or [Procfile](Procfile).
5. In **Variables**, add `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_KEY`, `JWT_SECRET`.
6. Go to **Settings** → **Networking** → **Generate Domain** to get your public live URL.

---

## Option 3: Deploy with Docker / Fly.io / Any Cloud VM

The project includes a production multi-stage [Dockerfile](Dockerfile):

```bash
# Build the Docker image
docker build -t jan-nidhi-spotter .

# Run the container locally or on any server
docker run -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  -e SUPABASE_URL="your-supabase-url" \
  -e SUPABASE_KEY="your-supabase-key" \
  -e JWT_SECRET="your-secret" \
  jan-nidhi-spotter
```

---

## Verification After Deployment

Once live at your public URL (e.g. `https://your-app.onrender.com`):
1. **Frontend**: Open `https://your-app.onrender.com` in your browser. The citizen dashboard and navigation will load immediately.
2. **API Documentation**: Visit `https://your-app.onrender.com/docs` to test FastAPI interactive Swagger docs.
3. **Health Check**: Check `https://your-app.onrender.com/health` to confirm server status.
