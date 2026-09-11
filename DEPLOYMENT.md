# 🚀 Jan Nidhi Spotter — Deployment Guide

This guide explains how to deploy:
1. **Frontend** on **Vercel** (Vite + React SPA)
2. **Database** on **MongoDB Atlas** (Free M0 Cluster)
3. **Backend** on **Render** (FastAPI with MongoDB & Supabase Storage)

---

## 1. MongoDB Atlas Setup (Free Cloud Database)

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and sign in or create a free account.
2. Click **Create a Deployment** $\rightarrow$ select the **M0 Free Tier** (AWS or Google Cloud, choose your preferred region).
3. Under **Security Quickstart**:
   - **Database User**: Create a username (e.g. `jannidhi_admin`) and a password. **Remember or copy this password**.
   - **Network Access**: Add IP Address $\rightarrow$ select **Allow Access from Anywhere** (`0.0.0.0/0`) so Render and external servers can connect.
4. Click **Database** $\rightarrow$ **Connect** $\rightarrow$ choose **Drivers** (Python).
5. Copy the connection string. It looks like:
   ```text
   mongodb+srv://jannidhi_admin:<password>@cluster0.xxxxx.mongodb.net/jan_nidhi_db?retryWrites=true&w=majority
   ```
   *(Replace `<password>` with your actual database user password. If your password has special characters like `@` or `#`, URL-encode them).*

---

## 2. Backend Deployment on Render

1. Push your repository to **GitHub**.
2. Open your [Render Dashboard](https://dashboard.render.com).
3. If creating a new service: Click **New +** $\rightarrow$ **Web Service** $\rightarrow$ connect your repository.
4. Configure the settings:
   - **Name**: `jan-nidhi-spotter`
   - **Runtime**: `Python`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
5. In the **Environment Variables** section, add:

| Key | Value / Example |
|---|---|
| `MONGODB_URI` | `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/jan_nidhi_db?retryWrites=true&w=majority` |
| `SUPABASE_URL` | `https://wzbcxoeygqmofztrerqo.supabase.co` |
| `SUPABASE_KEY` | `sb_secret_RazVFnyniFmSOWCNmkxaag_LSmri5Sn` |
| `SUPABASE_BUCKET` | `citizen-proofs` |
| `JWT_SECRET` | Any random 32+ character string (or click Generate) |
| `CORS_ORIGINS` | `*` |
| `PYTHON_VERSION` | `3.11.9` |

6. Click **Save Changes** (or **Deploy Web Service**).
7. Once deployed, Render will provide your live backend URL (e.g., `https://jan-nidhi-spotter.onrender.com`).
   - Test it by visiting `https://jan-nidhi-spotter.onrender.com/health` or `https://jan-nidhi-spotter.onrender.com/docs`.

---

## 3. Frontend Deployment on Vercel

1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your **`jan-nidhi-spotter`** GitHub repository.
4. In the Project Configuration screen:
   - **Framework Preset**: Vite
   - **Root Directory**: Click `Edit` and select `frontend` (the root `vercel.json` also auto-detects this if left at root).
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand **Environment Variables** and add:

| Key | Value |
|---|---|
| `VITE_API_URL` | Your Render backend URL (e.g. `https://jan-nidhi-spotter.onrender.com`) |

6. Click **Deploy**.
7. Vercel will build and deploy your React frontend in under 30 seconds, giving you a live production domain (e.g., `https://jan-nidhi-spotter.vercel.app`).
8. The included [frontend/vercel.json](frontend/vercel.json) automatically handles SPA route rewrites so deep navigation (e.g. `/admin`, `/login`) never returns 404.

---

## 4. Default Seeded Credentials

When the backend starts with MongoDB, it automatically seeds initial admin accounts:
- **Admin Username**: `admin`
- **Admin Password**: `admin`
*(Or Email: `admin@gg` / Password: `admin`)*
