# 🚀 Deploy to AWS Elastic Beanstalk

This guide will help you deploy your Django trading dashboard to **AWS Elastic Beanstalk** with:
- ✅ **GitHub integration** (auto-deploy on push)
- ✅ **Auto SSL/HTTPS** (via Application Load Balancer)
- ✅ **Firewall/Security Groups** (built-in AWS security)
- ✅ **Auto-scaling** (handles traffic spikes)

---

## 📋 Prerequisites

1. **AWS Account** (free tier eligible)
2. **GitHub account** with your code pushed
3. **Domain name** (optional, but recommended)

---

## 🎯 Step-by-Step Deployment

### **Step 1: Prepare Your Code**

Your project already has the necessary files:
- ✅ `.ebextensions/` - Elastic Beanstalk configuration
- ✅ `Procfile` - Gunicorn server command
- ✅ `requirements.txt` - Includes gunicorn and whitenoise

**Make sure your code is pushed to GitHub.**

---

### **Step 2: Create AWS Elastic Beanstalk Application**

1. Go to [AWS Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk/)
2. Click **"Create Application"**
3. Fill in:
   - **Application name**: `trading-dashboard` (or your choice)
   - **Platform**: `Python`
   - **Platform branch**: `Python 3.12` (or latest)
   - **Platform version**: Latest recommended

4. Click **"Create application"**

---

### **Step 3: Create Environment**

1. In your new application, click **"Create environment"**
2. Choose **"Web server environment"**
3. Configure:
   - **Environment name**: `trading-dashboard-prod`
   - **Domain**: Leave default (or use your custom domain later)
   - **Description**: "Trading Dashboard Production"

4. **Platform**: Python 3.12 (or latest)

5. **Application code**: 
   - Choose **"Upload your code"**
   - Select **"Public source code repository"**
   - Connect your **GitHub account**
   - Select your repository and branch (usually `main` or `master`)

6. Click **"Create environment"** (takes 5-10 minutes)

---

### **Step 4: Configure Environment Variables**

Once your environment is created:

1. Go to **Configuration** → **Software** → **Edit**
2. Add these **Environment properties**:

```
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-env.elasticbeanstalk.com
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=your-rds-endpoint.region.rds.amazonaws.com
DATABASE_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

**Generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

3. Click **"Apply"**

---

### **Step 5: Set Up Database (RDS PostgreSQL)**

1. In AWS Console, go to **RDS** → **Create database**
2. Choose:
   - **Engine**: PostgreSQL
   - **Template**: Free tier (if eligible) or Production
   - **DB instance identifier**: `trading-dashboard-db`
   - **Master username**: `postgres` (or your choice)
   - **Master password**: (strong password)
   - **DB instance class**: `db.t3.micro` (free tier) or larger

3. **Connectivity**: 
   - ✅ **Publicly accessible**: Yes (or No if using VPC)
   - **VPC**: Same as your Elastic Beanstalk environment

4. Click **"Create database"**

5. **Update your environment variables** with the RDS endpoint:
   - Go to RDS → Your database → **Connectivity & security**
   - Copy the **Endpoint** (e.g., `trading-dashboard-db.xxxxx.us-east-1.rds.amazonaws.com`)
   - Update `DATABASE_HOST` in Elastic Beanstalk environment variables

---

### **Step 6: Enable HTTPS (Auto SSL)**

1. Go to **Configuration** → **Load balancer** → **Edit**
2. Under **Listeners**, add:
   - **Port**: `443`
   - **Protocol**: `HTTPS`
   - **SSL certificate**: Request a new certificate (or use ACM certificate)
   - **SSL policy**: `ELBSecurityPolicy-TLS-1-2-2017-01`

3. **Redirect HTTP to HTTPS**:
   - Add listener on port `80` (HTTP)
   - Set **Default process** → **Redirect to HTTPS**

4. Click **"Apply"**

---

### **Step 7: Configure Custom Domain (Optional)**

1. In **Configuration** → **Load balancer** → **Edit**
2. Under **Processes**, add your domain to the **Default process**
3. In your domain registrar (Namecheap, GoDaddy, etc.):
   - Add **CNAME record**:
     - **Name**: `www` (or `@` for root)
     - **Value**: `your-env.elasticbeanstalk.com`
   - Or use **Route 53** (AWS DNS) for easier management

---

### **Step 8: Deploy Updates**

**Every time you push to GitHub**, Elastic Beanstalk will:
- ✅ Automatically detect changes
- ✅ Build your application
- ✅ Run migrations
- ✅ Restart the server

**Or manually deploy:**
1. Go to **Environment** → **Upload and deploy**
2. Upload a ZIP of your code, or connect to GitHub

---

## 🔒 Security Features (Already Included)

✅ **Security Groups**: Only allows HTTP/HTTPS traffic (ports 80, 443)  
✅ **HTTPS/SSL**: Encrypted connections  
✅ **Firewall**: AWS security groups block unauthorized access  
✅ **Auto-scaling**: Handles traffic spikes automatically  
✅ **Health checks**: Monitors your app and restarts if needed  

---

## 📧 Email Setup (SendGrid Example)

1. Sign up at [SendGrid](https://sendgrid.com/) (free tier: 100 emails/day)
2. Create an **API Key**
3. Add to environment variables:
   ```
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   ```

---

## 🧪 Test Your Deployment

1. Visit your Elastic Beanstalk URL: `http://your-env.elasticbeanstalk.com`
2. Test registration → email verification → trial start
3. Check logs: **Logs** → **Request logs** → **Last 100 lines**

---

## 💰 Cost Estimate

- **Elastic Beanstalk**: Free (just pay for EC2 instance)
- **EC2 t3.micro**: ~$7-10/month (free tier: 750 hours/month for 12 months)
- **RDS PostgreSQL db.t3.micro**: ~$15/month (free tier: 750 hours/month for 12 months)
- **Data transfer**: First 1GB free, then ~$0.09/GB

**Total**: ~$0-10/month (with free tier) or ~$25-30/month (without free tier)

---

## 🐛 Troubleshooting

**502 Bad Gateway:**
- Check logs: **Logs** → **Request logs**
- Verify `SECRET_KEY` and `ALLOWED_HOSTS` are set correctly

**Static files not loading:**
- Run `python manage.py collectstatic` locally and commit `staticfiles/`
- Or check `.ebextensions/02_commands.config` is running

**Database connection errors:**
- Verify RDS security group allows connections from Elastic Beanstalk security group
- Check `DATABASE_HOST` is correct (no `http://` prefix)

**Migrations not running:**
- Check `.platform/hooks/postdeploy/01_migrate.sh` exists and is executable
- Or run manually: SSH into instance and run `python manage.py migrate`

---

## 📚 Additional Resources

- [AWS Elastic Beanstalk Django Guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)

---

**🎉 You're live!** Your site is now accessible at your Elastic Beanstalk URL with auto SSL, firewall, and GitHub auto-deployment.

