# SellerZone — Free Deployment Guide

> **Important Cost Note**: **Railway no longer offers a free tier** (it requires a minimum $5/month subscription). **Render offers a 100% Free Tier ($0/month)** with no credit card required. This guide shows you how to deploy completely free on **Render** (and also includes Railway instructions if you ever upgrade).

---

## Architecture Overview
- **Application Backend & Frontend**: Flask serving the dynamic API and static files (`/` and `/admin`).
- **Database & Storage**: Supabase (Free tier PostgreSQL + Auth + Storage).
- **Hosting Platform**: Render Free Tier Web Service ($0).

---

## 🚀 Option 1: Deploy on Render (Recommended — 100% Free)

### Step 1: Push Code to GitHub
1. Make sure all files (including `render.yaml`, `start.py`, `Dockerfile`, `backend/`, and `frontend/`) are committed.
2. Push your project to a new GitHub repository:
   ```bash
   git add .
   git commit -m "Configure zero-cost deployment for Render"
   git push origin main
   ```

### Step 2: Create Free Account on Render
1. Go to [dashboard.render.com](https://dashboard.render.com) and sign up for free using your GitHub account.

### Step 3: Create Web Service
1. Click **New +** at the top right and select **Web Service**.
2. Under "Connect a repository", select your `sellerzone` GitHub repository.
3. Configure the following fields:
   - **Name**: `sellerzone` (or any name you prefer)
   - **Region**: Choose the region closest to you or your client (e.g., *Oregon (US West)* or *Frankfurt (EU)*)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start.py`
   - **Instance Type**: Select **Free ($0/month)**

4. Under **Advanced** → **Health Check Path**, enter:
   ```text
   /api/health
   ```

### Step 4: Add Environment Variables
Under **Environment Variables**, click **Add Environment Variable** and enter the following values:

| Key | Value / Source |
| :--- | :--- |
| `PYTHON_VERSION` | `3.12.0` |
| `SUPABASE_URL` | Your Supabase project URL (e.g. `https://xxxx.supabase.co`) |
| `SUPABASE_PUBLISHABLE_KEY` | Your Supabase anon / publishable key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase `service_role` secret key |
| `SUPABASE_STORAGE_BUCKET` | `product-images` |
| `ADMIN_PASSWORD` | Strong password of your choice for the `/admin` portal |
| `ADMIN_SECRET` | Any long random string (e.g. `sz-secret-key-99381`) |

*(Note: Never share your `SUPABASE_SERVICE_ROLE_KEY` publicly.)*

### Step 5: Deploy
1. Click **Create Web Service**.
2. Render will build and deploy the app. Once finished, you will receive your live URL:
   `https://sellerzone-xxxx.onrender.com`

---

## ⚡ Pro Tip: Preventing Cold Starts on Render Free Tier

On Render's Free tier, the web service spins down after 15 minutes of inactivity to save energy, and takes ~30-50 seconds to wake up on the first visit.

To make the site **instant and fast 24/7 for your client**:
1. Go to [cron-job.org](https://cron-job.org) or [uptimerobot.com](https://uptimerobot.com) (both 100% free).
2. Set up a free monitor/cron job that pings:
   ```text
   https://your-app-name.onrender.com/api/health
   ```
3. Set the interval to **every 10 minutes**.
4. This keeps the free server continuously warm and responsive at zero cost!

---

## 🚂 Option 2: Deploy on Railway (Paid — $5/mo minimum)

If you or your client have a budget for Railway:

1. Go to [railway.com](https://railway.com) and log in.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select `sellerzone`.
4. Railway will automatically detect `railway.json` and `Dockerfile`.
5. Under **Variables**, add:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_STORAGE_BUCKET`
   - `ADMIN_PASSWORD`
   - `ADMIN_SECRET`
6. Under **Settings → Networking**, click **Generate Domain**.

---

## 🗄️ Supabase Database Setup (One-time)

If starting with a fresh Supabase project:
1. Open your Supabase Dashboard → **SQL Editor**.
2. Run the SQL script found in `supabase/schema.sql`.
3. Go to **Storage** and ensure a public bucket named `product-images` exists.

---

## 🌐 URLs After Deployment

- **Main Storefront**: `https://your-app.onrender.com/`
- **Admin Dashboard**: `https://your-app.onrender.com/admin`
- **Health Check**: `https://your-app.onrender.com/api/health`

Log in to the Admin Dashboard using:
- **Password**: The value you set for `ADMIN_PASSWORD`.
