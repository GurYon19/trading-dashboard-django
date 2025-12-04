# 🚀 Render.com Quick Start Guide

**Deploy your Trading Dashboard in 10 minutes!**

---

## ✅ **Pre-Deployment Checklist**

Before deploying, make sure:

- [x] Code is pushed to GitHub
- [x] `requirements.txt` includes `gunicorn` and `whitenoise` ✅
- [x] `render.yaml` exists ✅
- [x] `SECRET_KEY` ready to generate
- [x] SendGrid account (for emails) - optional for now

---

## 🎯 **5-Minute Deployment Steps**

### **Step 1: Sign Up (1 minute)**

1. Go to **[render.com](https://render.com)**
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (recommended - easier)

---

### **Step 2: Create PostgreSQL Database (2 minutes)**

1. Click **"New +"** → **"PostgreSQL"**
2. Fill in:
   - **Name**: `trading-dashboard-db`
   - **Database**: `trading_dashboard`
   - **User**: `trading_user`
   - **Plan**: **Free** (or Starter $7/month)
3. Click **"Create Database"**
4. **Copy the "Internal Database URL"** (you'll need it)

---

### **Step 3: Create Web Service (2 minutes)**

1. Click **"New +"** → **"Web Service"**
2. Connect your **GitHub repository**
3. Select your repo and branch (`main`)

**Configure:**
- **Name**: `trading-dashboard`
- **Environment**: `Python 3`
- **Region**: Choose closest to you
- **Branch**: `main`

**Build & Start Commands:**
- **Build Command**: 
  ```
  pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
  ```
- **Start Command**: 
  ```
  gunicorn config.wsgi:application
  ```

---

### **Step 4: Add Environment Variables (2 minutes)**

In your **Web Service** → **Environment** tab, click **"Add Environment Variable"**:

**Required Variables:**

```
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=trading-dashboard.onrender.com
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Database (Auto-filled):**
- Click **"Link Database"** → Select `trading-dashboard-db`
- Render automatically sets `DATABASE_URL` ✅

**Optional (Email - add later):**
```
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

---

### **Step 5: Deploy! (5 minutes)**

1. Click **"Create Web Service"**
2. Render will automatically:
   - ✅ Clone your code
   - ✅ Install dependencies
   - ✅ Run migrations
   - ✅ Collect static files
   - ✅ Start your app
3. **Wait 5-10 minutes** for first deployment
4. Watch the **Logs** tab to see progress

---

### **Step 6: Create Superuser (1 minute)**

After deployment succeeds:

1. Go to **Web Service** → **Shell** tab
2. Run:
   ```bash
   python manage.py createsuperuser
   ```
3. Enter email, password

---

### **Step 7: Test! (1 minute)**

1. Visit: `https://trading-dashboard.onrender.com`
2. Test:
   - ✅ Homepage loads
   - ✅ Registration works
   - ✅ Login works
   - ✅ Purchase page works
   - ✅ Trial flow works

---

## 🎉 **You're Live!**

Your site is now at: `https://trading-dashboard.onrender.com`

**What Render does automatically:**
- ✅ SSL/HTTPS (free)
- ✅ Auto-deploy on git push
- ✅ Server management
- ✅ Monitoring
- ✅ Backups

---

## 🔄 **Auto-Deploy Setup**

**Every time you push to GitHub:**
1. Render detects changes
2. Automatically rebuilds
3. Deploys new version
4. Restarts service

**No manual deployment needed!**

---

## 🐛 **Common Issues & Fixes**

### **Build Fails:**
- Check **Logs** tab for error
- Verify `requirements.txt` is correct
- Make sure Python version is compatible

### **App Crashes:**
- Check **Logs** tab
- Verify `SECRET_KEY` is set
- Check `ALLOWED_HOSTS` includes your Render URL

### **Database Errors:**
- Verify database is linked
- Check `DATABASE_URL` is set
- Run migrations manually in Shell:
  ```bash
  python manage.py migrate
  ```

### **Static Files Not Loading:**
- Verify `collectstatic` ran in build command
- Check `STATIC_ROOT` is set in settings.py ✅
- Check WhiteNoise middleware is enabled ✅

---

## 📧 **Set Up Email (Optional - Later)**

1. Sign up at [sendgrid.com](https://sendgrid.com) (free tier: 100 emails/day)
2. Create **API Key**
3. Add to Render environment variables:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   ```
4. Redeploy (or it auto-deploys)

---

## 💰 **Cost**

- **Web Service**: **FREE** (750 hours/month = 24/7)
- **PostgreSQL**: **FREE** (first 90 days), then **$7/month**
- **Total**: **$0** → **$7/month** after 3 months

---

## 📚 **Useful Links**

- [Render Dashboard](https://dashboard.render.com)
- [Render Docs](https://render.com/docs)
- [Your App Logs](https://dashboard.render.com/web/YOUR_SERVICE_ID/logs)

---

## ✅ **Post-Deployment Checklist**

- [ ] Site loads at Render URL
- [ ] Registration works
- [ ] Login works
- [ ] Purchase page works
- [ ] Trial flow works
- [ ] Admin panel works (`/admin/`)
- [ ] Static files load (CSS, images)
- [ ] Database migrations ran successfully

---

## 🎯 **Next Steps**

1. **Test everything** - Make sure all features work
2. **Set up custom domain** (optional):
   - Settings → Custom Domains
   - Add your domain
   - Update DNS
3. **Set up email** (SendGrid) - For verification emails
4. **Monitor** - Check Metrics tab for performance

---

**That's it! Your trading dashboard is live!** 🚀

**Need help?** Check the **Logs** tab in Render dashboard for errors.

