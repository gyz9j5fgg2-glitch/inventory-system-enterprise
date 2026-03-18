#!/bin/bash
# install-app-ubuntu.sh - Ubuntu Web服务器安装脚本

set -e

# 配置变量 - 请根据实际情况修改
DB_HOST="${DB_HOST:-192.168.1.21}"
DB_PASSWORD="${DB_PASSWORD:-}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

echo "========================================"
echo "部署 EIMS 应用系统 (Ubuntu)"
echo "========================================"

if [ -z "$DB_PASSWORD" ] || [ -z "$REDIS_PASSWORD" ]; then
    echo "错误: 请设置DB_PASSWORD和REDIS_PASSWORD环境变量"
    echo "示例: DB_PASSWORD=xxx REDIS_PASSWORD=xxx ./install-app-ubuntu.sh"
    exit 1
fi

# 安装Docker
echo "[1/5] 安装Docker..."
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo systemctl enable docker
sudo systemctl start docker

# 创建应用目录
echo "[2/5] 下载应用代码..."
sudo mkdir -p /opt/eims
cd /opt/eims

if [ -d ".git" ]; then
    sudo git pull origin main
else
    sudo git clone https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise.git .
fi

# 创建环境配置文件
echo "[3/5] 配置应用..."
sudo tee deploy/.env > /dev/null <<EOF
# 数据库配置
DATABASE_URL=postgresql+asyncpg://inventory:${DB_PASSWORD}@${DB_HOST}:5432/inventory

# Redis配置
REDIS_URL=redis://:${REDIS_PASSWORD}@${DB_HOST}:6379/0
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@${DB_HOST}:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@${DB_HOST}:6379/2

# JWT配置
SECRET_KEY=$(openssl rand -base64 64 | tr -d "\n")
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LDAP配置（按需启用）
LDAP_ENABLED=false
LDAP_SERVER=ldap://ad.company.com:389
LDAP_BASE_DN=dc=company,dc=com

# 应用配置
DEBUG=false
LOG_LEVEL=INFO
EOF

# 启动应用
echo "[4/5] 启动应用容器..."
cd deploy
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 安装Nginx
echo "[5/5] 安装配置Nginx..."
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/eims > /dev/null <<'EOF'
upstream eims_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /opt/eims/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
        expires 1d;
    }
    
    location /api/ {
        proxy_pass http://eims_backend/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://eims_backend/health;
        access_log off;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/eims /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "========================================"
echo "应用部署完成!"
echo "========================================"
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo "健康检查: http://$(hostname -I | awk '{print $1}')/health"
echo ""
echo "检查状态:"
echo "  Docker: sudo docker ps"
echo "  Nginx: sudo systemctl status nginx"
echo "  日志: sudo docker logs -f deploy-api-1"
