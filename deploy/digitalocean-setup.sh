#!/bin/bash
# DigitalOcean Droplet Setup Script for Django Trading Dashboard
# Run this script on a fresh Ubuntu 22.04 droplet

set -e

echo "🚀 Setting up DigitalOcean Droplet for Django Trading Dashboard..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv python3-dev postgresql postgresql-contrib nginx git curl

# Install certbot for SSL
echo "🔒 Installing Certbot for SSL..."
sudo apt install -y certbot python3-certbot-nginx

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/trading-dashboard
sudo chown $USER:$USER /var/www/trading-dashboard

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
cd /var/www/trading-dashboard
python3 -m venv venv
source venv/bin/activate

# Install Gunicorn
pip install --upgrade pip
pip install gunicorn

echo "✅ Basic setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Clone your repository: git clone <your-repo-url> /var/www/trading-dashboard"
echo "2. Install requirements: pip install -r requirements.txt"
echo "3. Configure PostgreSQL database"
echo "4. Set up environment variables (.env file)"
echo "5. Run migrations: python manage.py migrate"
echo "6. Collect static files: python manage.py collectstatic"
echo "7. Configure Gunicorn service"
echo "8. Configure Nginx"
echo "9. Set up SSL with Let's Encrypt"
echo ""
echo "See DEPLOYMENT_DIGITALOCEAN.md for detailed instructions."

