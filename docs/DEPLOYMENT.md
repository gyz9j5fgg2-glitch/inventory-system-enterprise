# 企业级库存管理系统 - 部署文档

## 目录

1. [环境要求](#环境要求)
2. [快速开始](#快速开始)
3. [开发环境部署](#开发环境部署)
4. [测试环境部署](#测试环境部署)
5. [生产环境部署](#生产环境部署)
6. [LDAP/AD 配置](#ldapad-配置)
7. [备份与恢复](#备份与恢复)
8. [故障排查](#故障排查)

---

## 环境要求

### 硬件要求

| 环境 | CPU | 内存 | 磁盘 | 网络 |
|------|-----|------|------|------|
| 开发环境 | 2核 | 4GB | 20GB | 内网 |
| 测试环境 | 4核 | 8GB | 50GB | 内网 |
| 生产环境 | 8核+ | 16GB+ | 200GB+ SSD | 外网+内网 |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+/CentOS 7+) / Windows Server 2019+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **PostgreSQL**: 15+ (如不使用 Docker)
- **Redis**: 7+ (如不使用 Docker)
- **Nginx**: 1.20+ (生产环境)

---

## 快速开始

### 使用 Docker Compose 一键部署

```bash
# 1. 克隆代码
git clone https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise.git
cd inventory-system-enterprise/deploy

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库密码等

# 3. 启动服务
docker-compose up -d

# 4. 初始化数据库
docker-compose exec api alembic upgrade head

# 5. 创建初始管理员
docker-compose exec api python -c "
from app.database import AsyncSessionLocal
from app.models.user import User
import asyncio

async def init():
    async with AsyncSessionLocal() as db:
        admin = User(
            username='admin',
            email='admin@company.com',
            name='系统管理员',
            role='admin',
            is_active=True
        )
        admin.hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G'  # admin123
        db.add(admin)
        await db.commit()

asyncio.run(init())
"

# 6. 访问系统
# 前端: http://localhost
# API文档: http://localhost/api/docs
```

---

## 开发环境部署

### 方式一：Docker Compose（推荐）

```bash
cd deploy
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 方式二：本地开发

```bash
# 1. 安装 Python 3.11+
python --version

# 2. 创建虚拟环境
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装并启动 PostgreSQL
# 参考: https://www.postgresql.org/download/

# 5. 安装并启动 Redis
# 参考: https://redis.io/download

# 6. 配置环境变量
cp .env.example .env
# 编辑 .env

# 7. 数据库迁移
alembic upgrade head

# 8. 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 9. 启动 Celery Worker (另一个终端)
celery -A app.tasks worker --loglevel=info

# 10. 打开前端
# 直接用浏览器打开 frontend/index.html
# 或使用 Live Server 等工具
```

### 开发环境 .env 配置

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://inventory:inventory@localhost/inventory

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 调试模式
DEBUG=true
LOG_LEVEL=DEBUG

# LDAP (开发环境可禁用)
LDAP_ENABLED=false
```

---

## 测试环境部署

### 服务器准备

```bash
# Ubuntu 20.04 示例

# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 重启生效
newgrp docker
```

### 部署步骤

```bash
# 1. 创建应用目录
mkdir -p /opt/inventory-system
cd /opt/inventory-system

# 2. 克隆代码
git clone https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise.git .

# 3. 配置环境变量
cd deploy
cp .env.example .env

# 编辑 .env，设置强密码
vi .env
```

测试环境 .env 示例：

```env
# 数据库（使用强密码）
DATABASE_URL=postgresql+asyncpg://inventory:YourStrongPassword123@postgres/inventory
DB_PASSWORD=YourStrongPassword123

# Redis
REDIS_URL=redis://redis:6379/0

# JWT（使用随机生成的强密钥）
SECRET_KEY=your-random-32-char-secret-key-here

# LDAP（可选）
LDAP_ENABLED=false
# LDAP_SERVER=ldap://test-ad.company.com:389
# LDAP_BASE_DN=dc=company,dc=com

# 日志
LOG_LEVEL=INFO
```

```bash
# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f api

# 6. 初始化数据
docker-compose exec api alembic upgrade head

# 7. 配置 Nginx 反向代理（如果需要外部访问）
sudo apt install nginx -y
sudo vi /etc/nginx/sites-available/inventory
```

Nginx 配置：

```nginx
server {
    listen 80;
    server_name inventory-test.company.com;
    
    location / {
        root /opt/inventory-system/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 生产环境部署

### 高可用架构

```
                    [负载均衡器]
                         |
         +---------------+---------------+
         |                               |
    [Nginx 1]                     [Nginx 2]
         |                               |
    +----+----+                   +----+----+
    |         |                   |         |
[API 1]   [API 2]             [API 3]   [API 4]
    |         |                   |         |
    +----+----+                   +----+----+
         |                               |
    +----+----+                   +----+----+
    |         |                   |         |
[PostgreSQL Master]         [PostgreSQL Replica]
         |
    [Redis Cluster]
```

### 生产环境部署步骤

#### 1. 准备服务器

准备至少 3 台服务器：
- **Web 服务器** x2: 运行 API 和 Nginx
- **数据库服务器**: 运行 PostgreSQL 和 Redis

#### 2. 数据库服务器配置

```bash
# 安装 PostgreSQL 15
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-15 postgresql-15-pgpool2

# 配置 PostgreSQL
sudo vi /etc/postgresql/15/main/postgresql.conf
```

关键配置：

```conf
# 连接
listen_addresses = '*'
max_connections = 500

# 内存
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 20MB
maintenance_work_mem = 512MB

# WAL
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB

# 并发
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

```bash
# 配置访问权限
sudo vi /etc/postgresql/15/main/pg_hba.conf
```

添加：

```
host    inventory    inventory    10.0.0.0/8    scram-sha-256
```

```bash
# 重启 PostgreSQL
sudo systemctl restart postgresql

# 创建数据库和用户
sudo -u postgres psql
```

```sql
CREATE DATABASE inventory;
CREATE USER inventory WITH ENCRYPTED PASSWORD 'YourStrongPassword123';
GRANT ALL PRIVILEGES ON DATABASE inventory TO inventory;
\q
```

#### 3. 安装 Redis

```bash
sudo apt install redis-server
sudo vi /etc/redis/redis.conf
```

配置：

```conf
bind 0.0.0.0
requirepass YourRedisPassword123
maxmemory 2gb
maxmemory-policy allkeys-lru
```

```bash
sudo systemctl restart redis
```

#### 4. 部署应用服务器

```bash
# 在两台 Web 服务器上执行

mkdir -p /opt/inventory-system
cd /opt/inventory-system
git clone https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise.git .

cd deploy
cp .env.example .env.prod
```

生产环境 .env.prod：

```env
# 数据库（指向数据库服务器）
DATABASE_URL=postgresql+asyncpg://inventory:YourStrongPassword123@db-server:5432/inventory

# Redis（指向数据库服务器）
REDIS_URL=redis://:YourRedisPassword123@db-server:6379/0

# JWT
SECRET_KEY=your-production-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LDAP（生产环境启用）
LDAP_ENABLED=true
LDAP_SERVER=ldap://ad.company.com:389
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_DN=cn=admin,dc=company,dc=com
LDAP_PASSWORD=YourLDAPPassword

# 日志
DEBUG=false
LOG_LEVEL=WARNING

# Celery
CELERY_BROKER_URL=redis://:YourRedisPassword123@db-server:6379/1
CELERY_RESULT_BACKEND=redis://:YourRedisPassword123@db-server:6379/2
```

```bash
# 启动应用
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 5. 配置负载均衡

使用 Nginx 或硬件负载均衡器：

```nginx
upstream inventory_api {
    least_conn;
    server web1:8000 weight=5;
    server web2:8000 weight=5;
}

server {
    listen 443 ssl http2;
    server_name inventory.company.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        root /opt/inventory-system/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
        expires 1d;
    }
    
    location /api/ {
        proxy_pass http://inventory_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name inventory.company.com;
    return 301 https://$server_name$request_uri;
}
```

#### 6. 配置监控

```bash
# 安装 Prometheus + Grafana（可选）
# 或使用云监控服务
```

---

## LDAP/AD 配置

### Windows Active Directory 配置

#### 1. 创建服务账号

在 AD 中创建一个专用服务账号：
- **用户名**: `inventory-service`
- **密码**: 强密码
- **权限**: 域用户读取权限

#### 2. 创建用户组

创建以下组用于权限映射：
- `Inventory-Admins` → 系统管理员
- `Inventory-Warehouse-Managers` → 仓库管理员
- `Inventory-Approvers` → 审批人

#### 3. 配置系统

```bash
# 编辑 .env
LDAP_ENABLED=true
LDAP_SERVER=ldap://ad.company.com:389
# 或使用 ldaps://ad.company.com:636
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_DN=cn=inventory-service,ou=ServiceAccounts,dc=company,dc=com
LDAP_PASSWORD=YourServiceAccountPassword
```

#### 4. 测试连接

```bash
# 进入容器测试
docker-compose exec api python -c "
from app.services.ldap_auth import ldap_service
result = ldap_service.authenticate('testuser', 'password')
print(result)
"
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 连接失败 | 检查防火墙，确认 389/636 端口开放 |
| 认证失败 | 确认用户 DN 格式正确 |
| SSL 证书错误 | 导入 AD 证书到系统信任库 |

---

## 备份与恢复

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh - 每日自动备份

BACKUP_DIR="/backup/inventory"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份 PostgreSQL
docker exec inventory-postgres pg_dump -U inventory inventory | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 备份 Redis
docker exec inventory-redis redis-cli BGSAVE
docker cp inventory-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 删除旧备份
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.rdb" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

添加到 crontab：

```bash
# 每天凌晨 2 点备份
0 2 * * * /opt/inventory-system/deploy/backup.sh >> /var/log/inventory-backup.log 2>&1
```

### 恢复数据

```bash
# 恢复 PostgreSQL
gunzip < db_20240318_020000.sql.gz | docker exec -i inventory-postgres psql -U inventory -d inventory

# 恢复 Redis
docker cp redis_20240318_020000.rdb inventory-redis:/data/dump.rdb
docker restart inventory-redis
```

---

## 故障排查

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis

# 查看最近 100 行
docker-compose logs --tail=100 api
```

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker-compose ps postgres
docker-compose logs postgres

# 检查网络连接
docker-compose exec api ping postgres

# 检查数据库用户
docker-compose exec postgres psql -U inventory -c "\du"
```

#### 2. 端口被占用

```bash
# 查找占用端口的进程
sudo netstat -tulpn | grep :5432
sudo netstat -tulpn | grep :6379
sudo netstat -tulpn | grep :8000

# 停止冲突服务或修改端口映射
```

#### 3. 内存不足

```bash
# 查看内存使用
free -h
docker stats

# 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. 性能问题

```bash
# 查看数据库慢查询
docker-compose exec postgres psql -U inventory -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# 查看 Redis 内存使用
docker-compose exec redis redis-cli INFO memory

# API 性能分析
# 查看响应时间日志
```

### 联系支持

遇到问题请提交 Issue：
https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise/issues

---

## 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 备份数据库
./backup.sh

# 3. 执行数据库迁移
docker-compose exec api alembic upgrade head

# 4. 重启服务
docker-compose down
docker-compose up -d

# 5. 验证部署
curl http://localhost/health
```

---

**文档版本**: 1.0  
**最后更新**: 2024-03-18
