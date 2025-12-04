# 🚀 Deploy to DigitalOcean VPS

Complete guide to deploy your Django Trading Dashboard to a DigitalOcean Droplet.

---

## 📋 Prerequisites

1. **DigitalOcean account** ([Sign up here](https://m.do.co/c/your-referral-link))
2. **Domain name** (optional, but recommended)
3. **GitHub account** (for code repository)

---

## 🎯 Step 1: Create DigitalOcean Droplet

1. Go to [DigitalOcean Dashboard](https://cloud.digitalocean.com/)
2. Click **"Create"** → **"Droplets"**
3. Configure:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: **Regular** → **$6/month** (1GB RAM, 1 vCPU, 25GB SSD)
   - **Datacenter**: Choose closest to your users
   - **Authentication**: **SSH keys** (recommended) or Password
   - **Hostname**: `trading-dashboard` (or your choice)

4. Click **"Create Droplet"** (takes ~1 minute)

---

## 🔐 Step 2: Initial Server Setup

### **Connect via SSH:**

```bash
ssh root@YOUR_DROPLET_IP
```

### **Run Setup Script:**

```bash
# Download and run the setup script
curl -o setup.sh https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/deploy/digitalocean-setup.sh
chmod +x setup.sh
./setup.sh
```

**Or manually:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib nginx git curl certbot python3-certbot-nginx

# Create application directory
sudo mkdir -p /var/www/trading-dashboard
sudo chown $USER:$USER /var/www/trading-dashboard
```

---

## 🗄️ Step 3: Set Up PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE trading_dashboard;
CREATE USER trading_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE trading_user SET client_encoding TO 'utf8';
ALTER ROLE trading_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE trading_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE trading_dashboard TO trading_user;
\q
```

---

## 📥 Step 4: Deploy Your Code

```bash
cd /var/www/trading-dashboard

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Step 5: Configure Environment Variables

```bash
# Create .env file
nano /var/www/trading-dashboard/.env
```

**Add these variables:**

```env
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,YOUR_DROPLET_IP
DATABASE_NAME=trading_dashboard
DATABASE_USER=trading_user
DATABASE_PASSWORD=your_secure_password_here
DATABASE_HOST=localhost
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

---

## 🗃️ Step 6: Run Migrations & Collect Static Files

```bash
cd /var/www/trading-dashboard
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

---

## 🔧 Step 7: Configure Gunicorn

```bash
# Copy Gunicorn service file
sudo cp deploy/gunicorn.service /etc/systemd/system/trading-dashboard.service

# Edit the service file (if needed)
sudo nano /etc/systemd/system/trading-dashboard.service

# Start and enable Gunicorn
sudo systemctl daemon-reload
sudo systemctl start trading-dashboard
sudo systemctl enable trading-dashboard

# Check status
sudo systemctl status trading-dashboard
```

---

## 🌐 Step 8: Configure Nginx

```bash
# Copy Nginx configuration
sudo cp deploy/nginx.conf /etc/nginx/sites-available/trading-dashboard

# Edit configuration (replace your-domain.com)
sudo nano /etc/nginx/sites-available/trading-dashboard

# Enable site
sudo ln -s /etc/nginx/sites-available/trading-dashboard /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 🔒 Step 9: Set Up SSL (Let's Encrypt)

```bash
# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose redirect HTTP to HTTPS

# Test auto-renewal
sudo certbot renew --dry-run
```

**Certbot automatically renews certificates** (set up cron job if needed).

---

## 🔥 Step 10: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Check status
sudo ufw status
```

---

## 🔄 Step 11: Set Up Auto-Deploy (GitHub Actions)

1. **Add secrets to GitHub**:
   - Go to your repo → **Settings** → **Secrets and variables** → **Actions**
   - Add:
     - `DROPLET_IP`: Your droplet IP
     - `DROPLET_USER`: `root` or your user
     - `SSH_PRIVATE_KEY`: Your SSH private key

2. **Push to GitHub** - Auto-deploy will trigger!

---

## 📊 Step 12: Set Up Monitoring (Optional)

```bash
# Install monitoring tools
sudo apt install -y htop iotop

# Check system resources
htop
```

**Or use DigitalOcean's built-in monitoring** (free).

---

## 🔄 Step 13: Set Up Backups (Optional but Recommended)

```bash
# Enable DigitalOcean backups ($1/month)
# Go to Droplet → Settings → Backups → Enable
```

**Or manual snapshots:**
- Go to Droplet → **Snapshots** → **Take Snapshot**

---

## ✅ Step 14: Test Your Deployment

1. Visit `http://YOUR_DROPLET_IP` (or `https://your-domain.com`)
2. Test registration → email verification → trial start
3. Check logs:
   ```bash
   sudo journalctl -u trading-dashboard -f
   sudo tail -f /var/log/nginx/error.log
   ```

---

## 🐛 Troubleshooting

### **502 Bad Gateway:**
```bash
# Check Gunicorn status
sudo systemctl status trading-dashboard

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart trading-dashboard
sudo systemctl restart nginx
```

### **Static files not loading:**
```bash
# Recollect static files
cd /var/www/trading-dashboard
source venv/bin/activate
python manage.py collectstatic --noinput

# Check permissions
sudo chown -R www-data:www-data /var/www/trading-dashboard/staticfiles
```

### **Database connection errors:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
sudo -u postgres psql -d trading_dashboard
```

---

## 💰 Cost Breakdown

- **Droplet**: $6/month (1GB RAM)
- **Backups**: $1/month (optional)
- **Domain**: $12/year (optional)
- **Total**: **~$7/month** ($84/year)

---

## 🎉 You're Live!

Your trading dashboard is now running on a professional VPS with:
- ✅ Full root access (VPS control)
- ✅ Excellent infrastructure (SSD, fast networks)
- ✅ Free SSL (Let's Encrypt)
- ✅ Firewall protection
- ✅ Auto-deploy from GitHub
- ✅ Professional setup

**Visit**: `https://your-domain.com` 🚀

---

## 📚 Additional Resources

- [DigitalOcean Django Guide](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04)
- [Let's Encrypt Docs](https://letsencrypt.org/docs/)
- [Gunicorn Docs](https://gunicorn.org/)

