# Jan Nidhi Spotter Backend & Citizen Portal

A standalone FastAPI backend and interactive web portal for **citizen ground verification, photographic proof submissions, and XP gamification** for monitoring public works.

Citizens submit ground photographic proof with GPS coordinates and structure observations. The backend validates submissions, stores proof images in **Supabase Storage**, persists verification metadata in **PostgreSQL**, and awards **+150 XP** through an explicit deferred claim flow.

---

## Key Features

1. **Mandatory 6-Field Citizen Verification Form:**
   - Citizen Handle / ID *
   - Locality Name *
   - Structure Type * (Community Hall, Shelter, Solar Street Light, etc.)
   - Ground Observation * (Fully Built / Ready, Work in Progress, No Structure Found)
   - Location * (`[ Use My Current Location ]` with GPS coordinates capture)
   - Photo * (JPG, JPEG, PNG, WEBP, max 10MB with live preview)
2. **Deferred XP Flow:**
   - XP is **never** awarded prematurely upon form submit.
   - User receives a success screen and must explicitly click **`[ CLAIM 150 XP ]`**.
   - Backend fixed constant: `XP_PER_VERIFICATION = 150`.
   - **Duplicate XP Protection:** A verification cannot have XP claimed more than once.
3. **User Authentication & Dashboard:**
   - JWT authentication (`/auth/register`, `/auth/login`, `/auth/me`).
   - Citizen Dashboard with Level calculation (300 XP per level) and progress bar.
4. **My Submissions & Admin Portal:**
   - Citizen submission history with individual claim buttons.
   - Admin review interface (`Pending`, `Under Review`, `Verified`, `Rejected` with comments; XP is fixed and cannot be changed by Admin).
5. **Interactive Web Application:**
   - Modern dark-themed glassmorphism interface served directly at `http://127.0.0.1:8001/`.

---

## Environment Variables (.env)

```env
DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/jan_nidhi_db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
SUPABASE_BUCKET=citizen-proofs
JWT_SECRET=your-secret-key-2026
```

---

## Running the Application

```bash
# Windows:
venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

- **Web Portal:** [http://127.0.0.1:8001/](http://127.0.0.1:8001/) or [http://127.0.0.1:8001/portal](http://127.0.0.1:8001/portal)
- **Interactive Swagger UI:** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc:** [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register new account |
| `POST` | `/auth/login` | Log in and receive JWT token |
| `GET` | `/auth/me` | Current user profile & XP stats |

### Ground Verification & XP
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/verifications/` | Submit ground proof with all 6 mandatory fields (XP = 0) |
| `POST` | `/verifications/{id}/claim-xp` | Explicitly claim 150 XP (Duplicate-protected) |
| `GET` | `/verifications/` | List verifications (filters: `work_id`, `observation`, `review_status`) |
| `GET` | `/verifications/stats` | Aggregated metrics |
| `GET` | `/verifications/{id}` | Single verification record |
| `GET` | `/verifications/work/{work_id:path}` | Verifications by work ID |

### Citizen Dashboard & Admin Portal
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me/dashboard` | Citizen XP, level progression, and stats |
| `GET` | `/users/me/submissions` | History of citizen's ground evidence |
| `GET` | `/admin/verifications` | Admin view of all submissions with user details |
| `PATCH` | `/admin/verifications/{id}/review` | Admin review decision & notes (XP is fixed at 150) |

---

## Testing

Run the full end-to-end automated test suite:

```bash
venv\Scripts\python.exe test_workflow_v2.py
```
