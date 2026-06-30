# Deployment Guide - Render Hosting

## Free Hosting on Render.com

### Step 1: Push Project to GitHub ✅
Your project is already on GitHub: https://github.com/Eliot1001/land-_dispute_system

### Step 2: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

### Step 3: Deploy to Render
1. Go to Render Dashboard
2. Click **New Web Service**
3. Connect your GitHub repository: `Eliot1001/land-_dispute_system`
4. Fill in details:
   - **Name**: `land-dispute-system`
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn trackingsystem.wsgi:application`
   - **Plan**: Free tier

### Step 4: Add Environment Variables
In Render Dashboard → Environment:
```
DEBUG=False
SECRET_KEY=<generate-a-random-secret>
ALLOWED_HOSTS=yourdomain.onrender.com
DATABASE_URL=postgresql://...
```

### Step 5: Deploy Database
1. Render → PostgreSQL → New PostgreSQL
2. Copy DATABASE_URL
3. Add to Environment Variables
4. Run migrations

### Step 6: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Live URL
Your app will be at: `https://land-dispute-system.onrender.com`

---

## Alternative: Railway (Easiest)
1. Go to https://railway.app
2. Click "New Project"
3. "Deploy from GitHub"
4. Select your repository
5. Add PostgreSQL from Plugins
6. Done! (takes ~2 minutes)

## Local Development Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```
