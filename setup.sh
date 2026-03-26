#!/bin/bash

#############################################
# DialGenix.ai - One-Click Deployment Script
# 
# Usage: bash setup.sh
#############################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "=============================================="
echo "   DialGenix.ai Automated Deployment"
echo "=============================================="
echo -e "${NC}"

# Collect required information
echo -e "${YELLOW}Please provide the following information:${NC}"
echo ""

read -p "GitHub repo URL (e.g., https://github.com/user/repo.git): " GITHUB_REPO
read -p "Your domain (e.g., dialgenix.ai): " DOMAIN
read -p "Your email (for SSL certificate): " EMAIL

echo ""
echo -e "${YELLOW}Now enter your API keys:${NC}"
echo ""

read -p "EMERGENT_API_KEY: " EMERGENT_KEY
read -p "TWILIO_ACCOUNT_SID: " TWILIO_SID
read -p "TWILIO_AUTH_TOKEN: " TWILIO_TOKEN
read -p "TWILIO_PHONE_NUMBER (e.g., +1234567890): " TWILIO_PHONE
read -p "ELEVENLABS_API_KEY: " ELEVENLABS_KEY
read -p "STRIPE_SECRET_KEY (live key): " STRIPE_KEY
read -p "STRIPE_WEBHOOK_SECRET (enter 'skip' if setting up later): " STRIPE_WEBHOOK

# Generate random JWT secret
JWT_SECRET=$(openssl rand -hex 32)

echo ""
echo -e "${GREEN}Starting deployment...${NC}"
echo ""

# Step 1: Update system
echo -e "${CYAN}[1/12] Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install dependencies
echo -e "${CYAN}[2/12] Installing dependencies...${NC}"
sudo apt install -y curl git build-essential nginx certbot python3-certbot-nginx

# Step 3: Install Node.js
echo -e "${CYAN}[3/12] Installing Node.js 20...${NC}"
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Step 4: Install Python
echo -e "${CYAN}[4/12] Installing Python 3.11...${NC}"
sudo apt install -y python3.11 python3.11-venv python3-pip

# Step 5: Install PM2
echo -e "${CYAN}[5/12] Installing PM2...${NC}"
sudo npm install -g pm2

# Step 6: Install MongoDB
echo -e "${CYAN}[6/12] Installing MongoDB...${NC}"
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Step 7: Clone repository
echo -e "${CYAN}[7/12] Cloning repository...${NC}"
sudo mkdir -p /var/www/dialgenix
cd /var/www/dialgenix
sudo git clone $GITHUB_REPO .
sudo chown -R $USER:$USER /var/www/dialgenix

# Step 8: Setup Backend
echo -e "${CYAN}[8/12] Setting up backend...${NC}"
cd /var/www/dialgenix/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Create backend .env
cat > .env << ENVEOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=dialgenix_prod
EMERGENT_API_KEY=$EMERGENT_KEY
TWILIO_ACCOUNT_SID=$TWILIO_SID
TWILIO_AUTH_TOKEN=$TWILIO_TOKEN
TWILIO_PHONE_NUMBER=$TWILIO_PHONE
ELEVENLABS_API_KEY=$ELEVENLABS_KEY
STRIPE_SECRET_KEY=$STRIPE_KEY
STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK
JWT_SECRET=$JWT_SECRET
ENVEOF

# Step 9: Setup Frontend
echo -e "${CYAN}[9/12] Setting up frontend (this may take a few minutes)...${NC}"
cd /var/www/dialgenix/frontend
echo "REACT_APP_BACKEND_URL=https://$DOMAIN" > .env
npm install --legacy-peer-deps
npm run build

# Step 10: Configure Nginx
echo -e "${CYAN}[10/12] Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/dialgenix > /dev/null << NGINXEOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        root /var/www/dialgenix/frontend/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
}
NGINXEOF

sudo ln -sf /etc/nginx/sites-available/dialgenix /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Step 11: Start Backend with PM2
echo -e "${CYAN}[11/12] Starting backend with PM2...${NC}"
cd /var/www/dialgenix/backend
source venv/bin/activate

cat > ecosystem.config.js << PM2EOF
module.exports = {
  apps: [{
    name: 'dialgenix-backend',
    script: 'venv/bin/uvicorn',
    args: 'server:app --host 0.0.0.0 --port 8001',
    cwd: '/var/www/dialgenix/backend',
    interpreter: 'none',
    env: {
      PATH: '/var/www/dialgenix/backend/venv/bin:' + process.env.PATH
    }
  }]
};
PM2EOF

pm2 start ecosystem.config.js
pm2 save

# Step 12: Setup SSL
echo -e "${CYAN}[12/12] Setting up SSL certificate...${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Make sure your domain DNS is pointing to this server!${NC}"
echo -e "${YELLOW}A record for @ -> $(curl -s ifconfig.me)${NC}"
echo -e "${YELLOW}A record for www -> $(curl -s ifconfig.me)${NC}"
echo ""
read -p "Is your DNS configured? (y/n): " DNS_READY

if [ "$DNS_READY" = "y" ]; then
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $EMAIL --redirect
else
    echo -e "${YELLOW}Skipping SSL. Run this later: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN${NC}"
fi

# Setup PM2 startup
echo -e "${CYAN}Setting up PM2 auto-start...${NC}"
pm2 startup | tail -1 | bash
pm2 save

# Done!
echo ""
echo -e "${GREEN}=============================================="
echo "   DEPLOYMENT COMPLETE!"
echo "==============================================${NC}"
echo ""
echo -e "Your app is now live at: ${CYAN}https://$DOMAIN${NC}"
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Configure Stripe webhook at: https://dashboard.stripe.com/webhooks"
echo "   Endpoint: https://$DOMAIN/api/stripe/webhook"
echo "   Then update STRIPE_WEBHOOK_SECRET in /var/www/dialgenix/backend/.env"
echo ""
echo "2. Configure Twilio webhooks at: https://console.twilio.com"
echo "   Voice URL: https://$DOMAIN/api/twilio/voice"
echo "   Status URL: https://$DOMAIN/api/twilio/status"
echo ""
echo -e "${YELLOW}USEFUL COMMANDS:${NC}"
echo "  View logs:     pm2 logs dialgenix-backend"
echo "  Restart app:   pm2 restart dialgenix-backend"
echo "  Check status:  pm2 status"
echo ""
echo -e "${GREEN}Deployment successful!${NC}"
