# 🚀 Render Deployment - Step-by-Step Troubleshooting Guide

## ⚠️ **If Render Didn't Deploy - Follow These Steps**

---

## ✅ **Step 1: Verify Your Code is on GitHub**

1. Go to your GitHub repository
2. Make sure `render.yaml` is in the root directory
3. Make sure `requirements.txt` exists
4. Make sure you've pushed all changes:
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

---

## ✅ **Step 2: Sign Up / Log In to Render**

1. Go to **[render.com](https://render.com)**
2. Click **"Get Started for Free"** or **"Log In"**
3. Sign up with **GitHub** (recommended - easier integration)
4. Authorize Render to access your GitHub repositories

---

## ✅ **Step 3: Create PostgreSQL Database FIRST**

**IMPORTANT: Create the database BEFORE the web service!**

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Fill in:
   - **Name**: `trading-dashboard-db` (must match render.yaml)
   - **Database**: `trading_dashboard`
   - **User**: `trading_user`
   - **Plan**: **Free** (or Starter $7/month)
3. Click **"Create Database"**
4. **Wait for it to finish creating** (takes 1-2 minutes)
5. **Copy the "Internal Database URL"** (you might need it)

---

## ✅ **Step 4: Create Web Service**

### **Option A: Using render.yaml (Auto-Detection) - RECOMMENDED**

1. Click **"New +"** → **"Web Service"**
2. Connect your **GitHub repository**
3. Select your repository: `trading-dashboard-django`
4. Select branch: `main`
5. **Render should auto-detect `render.yaml`** ✅
   - If it does, you'll see fields pre-filled
   - Click **"Apply"** or **"Create Web Service"**
6. If it doesn't auto-detect, use **Option B** below

### **Option B: Manual Configuration**

If `render.yaml` isn't detected, manually configure:

**Basic Settings:**
- **Name**: `trading-dashboard`
- **Environment**: `Python 3`
- **Region**: Choose closest to you
- **Branch**: `main`

**Build Command:**
```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
```

**Start Command:**
```
gunicorn config.wsgi:application --workers 2 --timeout 120
```

---

## ✅ **Step 5: Link Database**

**CRITICAL: You must link the database!**

1. In your **Web Service** settings
2. Scroll down to **"Environment"** section
3. Find **"Link Database"** or **"Add Database"**
4. Select `trading-dashboard-db` (the one you created)
5. Render will automatically set `DATABASE_URL` ✅

---

## ✅ **Step 6: Add Environment Variables**

Go to **Web Service** → **Environment** tab → **"Add Environment Variable"**

### **Required Variables:**

1. **SECRET_KEY** (REQUIRED - app won't start without this!)
   - Generate one:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```
   - Copy the output
   - Add as: `SECRET_KEY=<paste-generated-key>`

2. **DEBUG**
   - Value: `False`

3. **ALLOWED_HOSTS**
   - Value: `trading-dashboard.onrender.com` (or your actual Render URL)
   - **Important**: After deployment, check your actual URL in Render dashboard and update this!

4. **EMAIL_BACKEND** (for now, use console - no email setup needed)
   - Value: `django.core.mail.backends.console.EmailBackend`

### **Optional (Email - add later if needed):**
```
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

---

## ✅ **Step 7: Deploy**

1. Click **"Create Web Service"** (or **"Save Changes"** if editing)
2. **Watch the Logs tab** - this shows what's happening
3. **Wait 5-10 minutes** for first deployment
4. The build process will:
   - ✅ Clone your code
   - ✅ Install Python dependencies
   - ✅ Run `collectstatic` (gather static files)
   - ✅ Run `migrate` (set up database tables)
   - ✅ Start gunicorn server

---

## 🐛 **Troubleshooting Common Issues**

### **Issue 1: "Service Not Found" or "No Services"**

**Problem**: You haven't created the web service yet.

**Solution**: 
- Go to Render dashboard
- Click **"New +"** → **"Web Service"**
- Follow Step 4 above

---

### **Issue 2: Build Fails**

**Check the Logs tab** - look for error messages:

**Common errors:**

1. **"Module not found"** or **"No module named X"**
   - **Fix**: Check `requirements.txt` includes all dependencies
   - Verify all packages are listed

2. **"SECRET_KEY not set"**
   - **Fix**: Add `SECRET_KEY` environment variable (Step 6)

3. **"Database connection failed"**
   - **Fix**: Make sure database is created AND linked (Step 3 & 5)
   - Check `DATABASE_URL` is set in Environment tab

4. **"collectstatic failed"**
   - **Fix**: Usually not critical, but check `STATIC_ROOT` in settings.py
   - Should be: `STATIC_ROOT = BASE_DIR / "staticfiles"`

5. **"migrate failed"**
   - **Fix**: Check database is linked
   - Check `DATABASE_URL` is set
   - You can skip migrations in build and run manually later

---

### **Issue 3: App Crashes After Deployment**

**Check the Logs tab** for runtime errors:

1. **"DisallowedHost" error**
   - **Fix**: Update `ALLOWED_HOSTS` with your actual Render URL
   - Find your URL in Render dashboard (e.g., `trading-dashboard-xyz.onrender.com`)
   - Add it to environment variables

2. **"SECRET_KEY" error**
   - **Fix**: Add `SECRET_KEY` environment variable

3. **"Database connection" error**
   - **Fix**: Verify database is linked
   - Check `DATABASE_URL` exists in Environment tab

---

### **Issue 4: render.yaml Not Detected**

**If Render doesn't auto-detect render.yaml:**

1. **Check file location**: `render.yaml` must be in the **root** of your repository
2. **Check file name**: Must be exactly `render.yaml` (not `render.yml`)
3. **Check it's committed**: Make sure `render.yaml` is pushed to GitHub
4. **Manual setup**: Use Option B in Step 4 to configure manually

---

### **Issue 5: "Database Not Found"**

**Problem**: Database name in `render.yaml` doesn't match created database.

**Solution**:
1. Check database name in Render dashboard
2. Update `render.yaml` to match, OR
3. Create database with exact name: `trading-dashboard-db`

---

## ✅ **Step 8: Verify Deployment**

After deployment succeeds:

1. **Check Status**: Should show "Live" in Render dashboard
2. **Visit URL**: Click the URL shown in Render (e.g., `https://trading-dashboard.onrender.com`)
3. **Check Logs**: Go to **Logs** tab - should see gunicorn running
4. **Test Site**: Try visiting homepage

---

## ✅ **Step 9: Create Superuser (Admin Access)**

After successful deployment:

1. Go to **Web Service** → **Shell** tab
2. Click **"Open Shell"**
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter:
   - Email address
   - Password (twice)
5. Visit `https://your-app.onrender.com/admin/` to log in

---

## 📋 **Quick Checklist**

Before deploying, make sure:

- [ ] Code is pushed to GitHub
- [ ] `render.yaml` exists in root directory
- [ ] `requirements.txt` exists and has all dependencies
- [ ] PostgreSQL database is created (`trading-dashboard-db`)
- [ ] Web service is created
- [ ] Database is linked to web service
- [ ] `SECRET_KEY` environment variable is set
- [ ] `DEBUG=False` is set
- [ ] `ALLOWED_HOSTS` includes your Render URL
- [ ] Build command includes migrations
- [ ] Start command is correct

---

## 🆘 **Still Having Issues?**

1. **Check Logs Tab**: This is your best friend - it shows exactly what's wrong
2. **Check Environment Variables**: Make sure all required vars are set
3. **Verify Database**: Make sure it's created AND linked
4. **Check Render Status Page**: [status.render.com](https://status.render.com)

---

## 📞 **Need More Help?**

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **Check Logs**: Always check the Logs tab first!

---

**Remember**: First deployment takes 5-10 minutes. Be patient and watch the Logs tab! 🚀

