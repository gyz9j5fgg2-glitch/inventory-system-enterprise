#!/bin/bash
# install-db-ubuntu.sh - Ubuntu数据库服务器安装脚本

set -e

echo "========================================"
echo "安装 PostgreSQL 15 + Redis (Ubuntu)"
echo "========================================"

# 安装PostgreSQL
echo "[1/4] 安装PostgreSQL 15..."
sudo apt update
sudo apt install -y curl ca-certificates gnupg

# 添加PostgreSQL APT仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
sudo apt update
sudo apt install -y postgresql-15 postgresql-15-contrib

# 配置PostgreSQL
echo "[2/4] 配置PostgreSQL..."
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/15/main/postgresql.conf
sudo sed -i "s/max_connections = 100/max_connections = 500/" /etc/postgresql/15/main/postgresql.conf

# 添加内存优化配置
sudo tee -a /etc/postgresql/15/main/conf.d/custom.conf > /dev/null <<EOF
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 20MB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
log_timezone = 'Asia/Shanghai'
datestyle = 'iso, ymd'
timezone = 'Asia/Shanghai'
EOF

# 配置访问权限
sudo tee -a /etc/postgresql/15/main/pg_hba.conf > /dev/null <<EOF
# EIMS应用访问
host    inventory    inventory    192.168.1.0/24    scram-sha-256
host    all          all          192.168.1.0/24    scram-sha-256
EOF

# 启动PostgreSQL
sudo systemctl enable postgresql-15
sudo systemctl restart postgresql-15

# 创建数据库和用户
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)

sudo -u postgres psql <<EOF
CREATE DATABASE inventory;
CREATE USER inventory WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE inventory TO inventory;
ALTER USER inventory WITH SUPERUSER;
\q

echo "PostgreSQL安装完成"

# 安装Redis
echo "[3/4] 安装Redis..."
sudo apt install -y redis-server

REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)

sudo sed -i 's/^bind 127.0.0.1 ::1/bind 0.0.0.0/' /etc/redis/redis.conf
sudo sed -i "s/^# requirepass.*/requirepass ${REDIS_PASSWORD}/" /etc/redis/redis.conf
sudo sed -i "s/^# maxmemory.*/maxmemory 2gb/" /etc/redis/redis.conf
sudo sed -i "s/^# maxmemory-policy.*/maxmemory-policy allkeys-lru/" /etc/redis/redis.conf
sudo sed -i 's/^# appendonly.*/appendonly yes/' /etc/redis/redis.conf

sudo systemctl enable redis-server
sudo systemctl restart redis-server

# 保存密码
echo "Database Password: ${DB_PASSWORD}" | sudo tee /root/db-password.txt
echo "Redis Password: ${REDIS_PASSWORD}" | sudo tee -a /root/db-password.txt
sudo chmod 600 /root/db-password.txt

echo "[4/4] 完成!"

echo "========================================"
echo "数据库安装完成"
echo "========================================"
echo ""
echo "PostgreSQL: 5432"
echo "Redis: 6379"
echo ""
echo "密码保存在: /root/db-password.txt"
echo ""
echo "数据库连接信息:"
echo "  主机: $(hostname -I | awk '{print $1}')"
echo "  端口: 5432"
echo "  数据库: inventory"
echo "  用户: inventory"
echo "  密码: ${DB_PASSWORD}"
