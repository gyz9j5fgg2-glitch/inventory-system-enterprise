# 企业级库存管理系统 - 现有虚拟化平台部署指南

**文档版本**: 1.0  
**适用场景**: 已有VMware vSphere/Proxmox/Hyper-V等虚拟化平台  
**部署目标**: 快速在现有虚拟化环境中部署EIMS应用系统  

---

## 目录

1. [环境要求确认](#环境要求确认)
2. [资源规划](#资源规划)
3. [虚拟机创建](#虚拟机创建)
4. [数据库部署](#数据库部署)
5. [应用部署](#应用部署)
6. [负载均衡配置](#负载均衡配置)
7. [验证与测试](#验证与测试)

---

## 环境要求确认

### 虚拟化平台兼容性

| 平台 | 版本要求 | 状态 |
|------|----------|------|
| VMware vSphere | 6.7+ | ✅ 支持 |
| Proxmox VE | 7.0+ | ✅ 支持 |
| Hyper-V | 2019+ | ✅ 支持 |
| 华为FusionCompute | 8.0+ | ✅ 支持 |
| H3C CAS | 5.0+ | ✅ 支持 |

### 现有环境检查清单

```bash
□ 虚拟化平台运行正常
□ 存储空间充足（建议预留1TB+）
□ 网络VLAN已配置（管理网、业务网、存储网）
□ 可分配IP地址充足
□ 有ISO镜像上传权限
□ 有虚拟机创建权限
□ 现有负载均衡/防火墙可配置新规则
```

---

## 资源规划

### 虚拟机规格

| 虚拟机名称 | 用途 | CPU | 内存 | 系统盘 | 数据盘 | IP地址 | 数量 |
|-----------|------|-----|------|--------|--------|--------|------|
| EIMS-DB | 数据库 | 8核 | 32GB | 100GB | 500GB | 192.168.1.21 | 1 |
| EIMS-WEB01 | Web服务1 | 4核 | 8GB | 100GB | - | 192.168.1.22 | 1 |
| EIMS-WEB02 | Web服务2 | 4核 | 8GB | 100GB | - | 192.168.1.23 | 1 |

**总资源需求**: 16核CPU / 48GB内存 / 800GB存储

### 网络规划

```
┌─────────────────────────────────────────┐
│           现有虚拟化平台                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ EIMS-DB │  │EIMS-WEB1│  │EIMS-WEB2│ │
│  │ .1.21   │  │  .1.22  │  │  .1.23  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
│       │            │            │      │
│       └────────────┼────────────┘      │
│                    │                   │
│              ┌─────┴─────┐             │
│              │ 虚拟交换机 │             │
│              │  VLAN100  │             │
│              └─────┬─────┘             │
└────────────────────┼────────────────────┘
                     │
              ┌──────┴──────┐
              │ 物理交换机   │
              │  ( trunk )  │
              └──────┬──────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────┴────┐ ┌────┴────┐ ┌────┴────┐
    │ 防火墙  │ │负载均衡 │ │ 管理PC  │
    └─────────┘ └────┬────┘ └─────────┘
                     │
              ┌──────┴──────┐
              │   用户访问   │
              └─────────────┘
```

---

## 虚拟机创建

### 方式一：使用OVF模板快速部署（推荐）

```bash
# 1. 下载预配置模板
curl -O https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise/releases/download/v1.0/eims-template.ova

# 2. 导入到vSphere
# 登录vCenter → 虚拟机 → 部署OVF模板 → 选择ova文件

# 3. 克隆虚拟机
# 右键模板 → 克隆 → 克隆到虚拟机
# 创建3个克隆: EIMS-DB, EIMS-WEB01, EIMS-WEB02

# 4. 修改克隆后的配置
# - 调整CPU/内存规格
# - 修改IP地址
# - 修改主机名
```

### 方式二：手动创建虚拟机

#### 创建数据库服务器 (EIMS-DB)

```
1. 登录虚拟化平台管理界面
2. 新建虚拟机
   - 名称: EIMS-DB
   - 操作系统: CentOS 8 / Ubuntu 22.04 LTS
   - CPU: 8核
   - 内存: 32GB
   - 硬盘1: 100GB (系统盘)
   - 硬盘2: 500GB (数据盘，精简置备)
   - 网卡: 连接到业务VLAN
3. 挂载操作系统ISO
4. 启动安装
```

#### 创建Web服务器 (EIMS-WEB01/02)

```
1. 新建虚拟机
   - 名称: EIMS-WEB01
   - 操作系统: CentOS 8 / Ubuntu 22.04 LTS
   - CPU: 4核
   - 内存: 8GB
   - 硬盘: 100GB
   - 网卡: 连接到业务VLAN
2. 同样方式创建EIMS-WEB02
```

### 操作系统安装要点

```bash
# 1. 选择最小化安装
# 2. 分区方案
/boot     1GB
/         50GB
/var      30GB
/home     10GB
swap      8GB

# 3. 网络配置
# EIMS-DB
IP: 192.168.1.21/24
Gateway: 192.168.1.1
DNS: 8.8.8.8

# EIMS-WEB01
IP: 192.168.1.22/24

# EIMS-WEB02
IP: 192.168.1.23/24

# 4. 安装后基础配置
# 更新系统
yum update -y  # CentOS
apt update && apt upgrade -y  # Ubuntu

# 配置时区
timedatectl set-timezone Asia/Shanghai

# 配置NTP
yum install -y chrony
systemctl enable chronyd --now

# 禁用防火墙（由外部防火墙管理）
systemctl stop firewalld
systemctl disable firewalld

# 配置SSH
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd
```

---

## 数据库部署

### 在EIMS-DB上执行

```bash
#!/bin/bash
# install-db.sh - 数据库一键安装脚本

set -e

echo "========================================"
echo "安装 PostgreSQL 15 + Redis"
echo "========================================"

# 安装PostgreSQL
if [ -f /etc/redhat-release ]; then
    # CentOS/RHEL
    sudo dnf module disable postgresql -y
    sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
    sudo dnf install -y postgresql15-server postgresql15-contrib
else
    # Ubuntu
    sudo apt update
    sudo apt install -y postgresql-15 postgresql-contrib
fi

# 初始化数据库
if [ -f /etc/redhat-release ]; then
    sudo /usr/pgsql-15/bin/postgresql-15-setup initdb
fi

# 配置PostgreSQL
sudo tee /var/lib/pgsql/15/data/postgresql.conf > /dev/null <<EOF
listen_addresses = '*'
port = 5432
max_connections = 500
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 20MB
maintenance_work_mem = 512MB
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
checkpoint_completion_target = 0.9
log_timezone = 'Asia/Shanghai'
datestyle = 'iso, ymd'
timezone = 'Asia/Shanghai'
lc_messages = 'en_US.UTF-8'
lc_monetary = 'en_US.UTF-8'
lc_numeric = 'en_US.UTF-8'
lc_time = 'en_US.UTF-8'
default_text_search_config = 'pg_catalog.english'
EOF

# 配置访问权限
sudo tee -a /var/lib/pgsql/15/data/pg_hba.conf > /dev/null <<EOF
# EIMS应用访问
host    inventory    inventory    192.168.1.0/24    scram-sha-256
host    all          all          127.0.0.1/32      trust
host    all          all          ::1/128           trust
EOF

# 启动PostgreSQL
sudo systemctl enable postgresql-15
sudo systemctl start postgresql-15

# 创建数据库和用户
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)
sudo -u postgres psql <<EOF
CREATE DATABASE inventory;
CREATE USER inventory WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE inventory TO inventory;
\q
EOF

# 保存密码
echo "Database Password: ${DB_PASSWORD}" > ~/db-password.txt
chmod 600 ~/db-password.txt

# 安装Redis
if [ -f /etc/redhat-release ]; then
    sudo dnf install -y redis
else
    sudo apt install -y redis-server
fi

# 配置Redis
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)
sudo tee /etc/redis/redis.conf > /dev/null <<EOF
bind 0.0.0.0
port 6379
requirepass ${REDIS_PASSWORD}
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
EOF

# 保存Redis密码
echo "Redis Password: ${REDIS_PASSWORD}" >> ~/db-password.txt

# 启动Redis
sudo systemctl enable redis
sudo systemctl start redis

echo "========================================"
echo "数据库安装完成"
echo "========================================"
echo "PostgreSQL: 5432"
echo "Redis: 6379"
echo "密码保存在: ~/db-password.txt"
```

执行安装：
```bash
chmod +x install-db.sh
./install-db.sh
```

---

## 应用部署

### 在EIMS-WEB01/02上执行

```bash
#!/bin/bash
# install-app.sh - 应用部署脚本

set -e

DB_HOST="192.168.1.21"
DB_PASSWORD="YourDBPassword"  # 从EIMS-DB获取
REDIS_PASSWORD="YourRedisPassword"  # 从EIMS-DB获取

echo "========================================"
echo "部署 EIMS 应用系统"
echo "========================================"

# 安装Docker
if [ -f /etc/redhat-release ]; then
    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    sudo apt update
    sudo apt install -y docker.io docker-compose
fi

sudo systemctl enable docker
sudo systemctl start docker

# 创建应用目录
sudo mkdir -p /opt/eims
cd /opt/eims

# 下载代码
sudo git clone https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise.git .

# 创建环境配置文件
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
cd deploy
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 安装Nginx
if [ -f /etc/redhat-release ]; then
    sudo dnf install -y nginx
else
    sudo apt install -y nginx
fi

# 配置Nginx
sudo tee /etc/nginx/nginx.conf > /dev/null <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    upstream eims_backend {
        server 127.0.0.1:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        location / {
            root /opt/eims/frontend;
            index index.html;
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
}
EOF

sudo systemctl enable nginx
sudo systemctl start nginx

echo "========================================"
echo "应用部署完成"
echo "========================================"
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo "健康检查: http://$(hostname -I | awk '{print $1}')/health"
```

执行部署：
```bash
chmod +x install-app.sh
./install-app.sh
```

---

## 负载均衡配置

### 现有负载均衡配置示例

#### F5 BIG-IP

```tcl
# 创建Pool
ltm pool EIMS-Pool {
    members {
        192.168.1.22:http { priority-group 2 }
        192.168.1.23:http { priority-group 2 }
    }
    monitor http
    load-balancing-mode least-connections-member
}

# 创建Virtual Server
ltm virtual EIMS-VIP {
    destination 192.168.1.10:http
    ip-protocol tcp
    pool EIMS-Pool
    profiles {
        http { }
        tcp { }
    }
    snat automap
}

# 健康检查
ltm monitor http http {
    defaults-from http
    interval 5
    timeout 16
    send "GET /health HTTP/1.0\r\n\r\n"
    recv "ok"
}
```

#### Nginx (软件负载均衡)

如果在虚拟化平台外需要软件负载均衡：

```nginx
upstream eims_backend {
    least_conn;
    server 192.168.1.22:80 weight=5;
    server 192.168.1.23:80 weight=5;
    
    keepalive 32;
}

server {
    listen 80;
    server_name inventory.company.com;
    
    location / {
        proxy_pass http://eims_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

---

## 验证与测试

### 健康检查

```bash
# 1. 检查数据库
curl http://192.168.1.21:5432  # 应拒绝连接（正常）
sudo -u postgres psql -c "SELECT version();"

# 2. 检查Redis
redis-cli -h 192.168.1.21 -a YourPassword ping  # 应返回PONG

# 3. 检查Web服务
curl http://192.168.1.22/health
curl http://192.168.1.23/health

# 4. 检查负载均衡
curl http://192.168.1.10/health
```

### 功能测试

```bash
# 1. 登录测试
# 访问 http://192.168.1.10
# 使用测试账号: admin / admin123

# 2. 业务流程测试
# - 申请人提交申请
# - 审批人审批
# - 仓库管理员发货确认
# - 验证库存扣减

# 3. 采购入库测试
# - 创建采购单
# - 确认入库
# - 验证库存增加
```

### 性能测试

```bash
# 使用ab或wrk进行压力测试
ab -n 10000 -c 100 http://192.168.1.10/api/v1/inventory/products

# 监控资源使用
top
iotop
iftop
```

---

## 快速部署命令汇总

```bash
# ========== 在EIMS-DB上执行 ==========
# 1. 复制安装脚本到服务器
scp install-db.sh root@192.168.1.21:/root/

# 2. SSH登录执行
ssh root@192.168.1.21
chmod +x install-db.sh
./install-db.sh

# 3. 获取密码
cat ~/db-password.txt

# ========== 在EIMS-WEB01/02上执行 ==========
# 1. 复制安装脚本
scp install-app.sh root@192.168.1.22:/root/
scp install-app.sh root@192.168.1.23:/root/

# 2. 编辑脚本，填入数据库密码
vi install-app.sh
# 修改: DB_PASSWORD="实际密码"
# 修改: REDIS_PASSWORD="实际密码"

# 3. 执行安装
ssh root@192.168.1.22 "chmod +x install-app.sh && ./install-app.sh"
ssh root@192.168.1.23 "chmod +x install-app.sh && ./install-app.sh"

# ========== 配置负载均衡 ==========
# 根据现有负载均衡设备配置
# 添加后端服务器: 192.168.1.22, 192.168.1.23
# 健康检查URL: /health
```

---

## 故障排查

### 常见问题

| 问题 | 排查命令 | 解决方案 |
|------|----------|----------|
| 数据库连接失败 | `telnet 192.168.1.21 5432` | 检查pg_hba.conf防火墙 |
| Redis连接失败 | `redis-cli ping` | 检查redis.conf bind配置 |
| 应用启动失败 | `docker logs <container>` | 检查.env配置 |
| 负载均衡异常 | `curl -v http://<ip>/health` | 检查后端服务状态 |

---

**部署完成！**

访问地址: http://<负载均衡VIP>
默认账号: admin / admin123
