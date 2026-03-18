# 企业级库存管理系统 - 完整部署手册

**版本**: v2.0.1-security  
**日期**: 2024-03-18  
**适用系统**: Ubuntu 22.04 LTS

---

## 目录

1. [服务器配置要求](#一服务器配置要求)
2. [系统环境准备](#二系统环境准备)
3. [基础环境搭建](#三基础环境搭建)
4. [数据库服务器部署](#四数据库服务器部署)
5. [Web服务器部署](#五web服务器部署)
6. [负载均衡配置](#六负载均衡配置)
7. [系统验证与测试](#七系统验证与测试)
8. [故障排查](#八故障排查)

---

## 一、服务器配置要求

### 1.1 硬件配置

#### 数据库服务器 (eims-db)

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4核 | 8核 |
| 内存 | 16GB | 32GB |
| 系统盘 | 100GB SSD | 100GB SSD |
| 数据盘 | 300GB | 500GB SSD |
| 网络 | 千兆网卡 | 千兆网卡 |

#### Web服务器 (eims-web01/02)

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 系统盘 | 50GB | 100GB SSD |
| 网络 | 千兆网卡 | 千兆网卡 |

### 1.2 网络规划

| 服务器 | IP地址 | 子网掩码 | 网关 | DNS |
|--------|--------|----------|------|-----|
| eims-db | 192.168.1.21 | 255.255.255.0 | 192.168.1.1 | 8.8.8.8 |
| eims-web01 | 192.168.1.22 | 255.255.255.0 | 192.168.1.1 | 8.8.8.8 |
| eims-web02 | 192.168.1.23 | 255.255.255.0 | 192.168.1.1 | 8.8.8.8 |
| 负载均衡VIP | 192.168.1.10 | - | - | - |

### 1.3 端口开放

| 服务 | 端口 | 源地址 | 说明 |
|------|------|--------|------|
| SSH | 22 | 管理网络 | 远程管理 |
| HTTP | 80 | 任意 | Web访问 |
| PostgreSQL | 5432 | 192.168.1.0/24 | 数据库 |
| Redis | 6379 | 192.168.1.0/24 | 缓存 |

---

## 二、系统环境准备

### 2.1 创建虚拟机

在现有虚拟化平台（VMware/Proxmox/Hyper-V）上创建3台虚拟机：

**步骤1：创建数据库服务器**
```
1. 登录虚拟化平台管理界面
2. 新建虚拟机
   - 名称: eims-db
   - 操作系统: Ubuntu 22.04 LTS Server (64位)
   - CPU: 8核
   - 内存: 32GB
   - 硬盘1: 100GB (系统盘)
   - 硬盘2: 500GB (数据盘)
   - 网络适配器: 桥接模式
3. 挂载Ubuntu 22.04 ISO镜像
4. 启动安装
```

**步骤2：创建Web服务器**
```
重复上述步骤，创建2台Web服务器：
- eims-web01: 4核/8GB/100GB
- eims-web02: 4核/8GB/100GB
```

### 2.2 Ubuntu系统安装

**步骤1：启动安装**
```
1. 选择语言: English
2. 选择键盘布局: English (US)
3. 选择安装类型: Ubuntu Server
4. 网络配置:
   - IPv4 Method: Manual
   - Subnet: 192.168.1.0/24
   - Address: 根据服务器填写
   - Gateway: 192.168.1.1
   - Name servers: 8.8.8.8,114.114.114.114
5. 代理配置: 留空
6. 镜像地址: 默认
7. 磁盘分区: Use entire disk
8. 创建用户:
   - Your name: Admin
   - Server name: eims-db (根据服务器填写)
   - Username: ubuntu
   - Password: 设置强密码
9. SSH配置: 勾选Install OpenSSH server
10. 等待安装完成，重启
```

**步骤2：基础配置（所有服务器执行）**

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 设置时区
sudo timedatectl set-timezone Asia/Shanghai

# 3. 安装常用工具
sudo apt install -y vim curl wget net-tools htop

# 4. 配置主机名
# eims-db执行:
sudo hostnamectl set-hostname eims-db
# eims-web01执行:
sudo hostnamectl set-hostname eims-web01
# eims-web02执行:
sudo hostnamectl set-hostname eims-web02

# 5. 配置hosts
sudo tee /etc/hosts << 'EOF'
127.0.0.1 localhost
192.168.1.21 eims-db
192.168.1.22 eims-web01
192.168.1.23 eims-web02
EOF

# 6. 禁用防火墙（由外部防火墙管理）
sudo ufw disable

# 7. 配置NTP时间同步
sudo apt install -y chrony
sudo systemctl enable chronyd --now

# 8. 重启
sudo reboot
```

---

## 三、基础环境搭建

### 3.1 数据库服务器基础配置

**步骤1：配置数据盘**

```bash
# 查看磁盘
lsblk

# 格式化数据盘（假设为/dev/sdb）
sudo mkfs.ext4 /dev/sdb

# 创建挂载点
sudo mkdir -p /data

# 挂载
sudo mount /dev/sdb /data

# 配置开机自动挂载
echo '/dev/sdb /data ext4 defaults 0 0' | sudo tee -a /etc/fstab

# 验证
sudo df -h
```

**步骤2：优化系统参数**

```bash
# 配置PostgreSQL内核参数
sudo tee -a /etc/sysctl.conf << 'EOF'
# PostgreSQL优化
kernel.shmmax = 17179869184
kernel.shmall = 4194304
vm.swappiness = 10
vm.dirty_ratio = 40
vm.dirty_background_ratio = 10
EOF

sudo sysctl -p

# 配置文件描述符限制
sudo tee -a /etc/security/limits.conf << 'EOF'
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
EOF
```

### 3.2 Web服务器基础配置

**步骤1：优化Docker存储**

```bash
# 创建Docker数据目录
sudo mkdir -p /data/docker

# 配置Docker使用数据目录（如需要）
# 编辑 /etc/docker/daemon.json
```

---

## 四、数据库服务器部署

### 4.1 安装PostgreSQL 15

**步骤1：执行自动化安装脚本**

```bash
# 下载安装脚本
curl -fsSL https://raw.githubusercontent.com/gyz9j5fgg2-glitch/inventory-system-enterprise/main/deploy/install-db-ubuntu.sh -o install-db.sh

# 执行安装
chmod +x install-db.sh
sudo ./install-db.sh
```

**或手动安装：**

```bash
# 1. 安装依赖
sudo apt update
sudo apt install -y curl ca-certificates gnupg

# 2. 添加PostgreSQL APT仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
sudo apt update

# 3. 安装PostgreSQL
sudo apt install -y postgresql-15 postgresql-15-contrib

# 4. 配置PostgreSQL
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/15/main/postgresql.conf
sudo sed -i "s/max_connections = 100/max_connections = 500/" /etc/postgresql/15/main/postgresql.conf

# 5. 添加性能优化配置
sudo tee /etc/postgresql/15/main/conf.d/custom.conf << 'EOF'
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 20MB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
EOF

# 6. 配置访问权限
sudo tee -a /etc/postgresql/15/main/pg_hba.conf << 'EOF'
host    inventory    inventory    192.168.1.0/24    scram-sha-256
host    all          all          192.168.1.0/24    scram-sha-256
EOF

# 7. 启动服务
sudo systemctl enable postgresql-15
sudo systemctl restart postgresql-15

# 8. 创建数据库和用户
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)
sudo -u postgres psql << EOF
CREATE DATABASE inventory;
CREATE USER inventory WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE inventory TO inventory;
ALTER USER inventory WITH SUPERUSER;
\q
EOF

echo "Database Password: ${DB_PASSWORD}" | sudo tee /root/db-password.txt
```

### 4.2 安装Redis

```bash
# 安装Redis
sudo apt install -y redis-server

# 配置Redis
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)

sudo sed -i 's/^bind 127.0.0.1 ::1/bind 0.0.0.0/' /etc/redis/redis.conf
sudo sed -i "s/^# requirepass.*/requirepass ${REDIS_PASSWORD}/" /etc/redis/redis.conf
sudo sed -i "s/^# maxmemory.*/maxmemory 2gb/" /etc/redis/redis.conf
sudo sed -i "s/^# maxmemory-policy.*/maxmemory-policy allkeys-lru/" /etc/redis/redis.conf

sudo systemctl enable redis-server
sudo systemctl restart redis-server

# 保存密码
echo "Redis Password: ${REDIS_PASSWORD}" | sudo tee -a /root/db-password.txt
sudo chmod 600 /root/db-password.txt
```

### 4.3 验证数据库安装

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql-15

# 检查Redis状态
sudo systemctl status redis-server

# 测试连接
sudo -u postgres psql -c "SELECT version();"
redis-cli -a "$(sudo cat /root/db-password.txt | grep 'Redis Password' | cut -d': ' -f2)" ping

# 查看密码
cat /root/db-password.txt
```

---

## 五、Web服务器部署

### 5.1 安装Docker

**在eims-web01和eims-web02上执行：**

```bash
# 1. 安装依赖
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 2. 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 3. 添加Docker APT仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. 安装Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 5. 启动Docker
sudo systemctl enable docker
sudo systemctl start docker

# 6. 验证安装
sudo docker --version
sudo docker compose version
```

### 5.2 部署应用

**步骤1：下载部署脚本**

```bash
# 下载安装脚本
curl -fsSL https://raw.githubusercontent.com/gyz9j5fgg2-glitch/inventory-system-enterprise/main/deploy/install-app-ubuntu.sh -o install-app.sh
chmod +x install-app.sh
```

**步骤2：执行部署（在eims-web01上）**

```bash
# 设置环境变量（从数据库服务器获取密码）
export DB_HOST="192.168.1.21"
export DB_PASSWORD="你的数据库密码"
export REDIS_PASSWORD="你的Redis密码"

# 执行安装
sudo -E ./install-app.sh
```

**步骤3：执行部署（在eims-web02上）**

```bash
# 同样的步骤在第二台Web服务器执行
export DB_HOST="192.168.1.21"
export DB_PASSWORD="你的数据库密码"
export REDIS_PASSWORD="你的Redis密码"

sudo -E ./install-app.sh
```

**或手动部署：**

```bash
# 1. 创建应用目录
sudo mkdir -p /opt/eims
cd /opt/eims

# 2. 下载代码
sudo git clone https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise.git .

# 3. 创建环境配置文件
sudo tee deploy/.env << EOF
DATABASE_URL=postgresql+asyncpg://inventory:${DB_PASSWORD}@192.168.1.21:5432/inventory
REDIS_URL=redis://:${REDIS_PASSWORD}@192.168.1.21:6379/0
SECRET_KEY=$(openssl rand -base64 64 | tr -d "\n")
DEBUG=false
EOF

# 4. 启动应用
cd deploy
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. 安装Nginx
sudo apt install -y nginx

# 6. 配置Nginx
sudo tee /etc/nginx/sites-available/eims << 'EOF'
upstream eims_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    
    location / {
        proxy_pass http://eims_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/eims /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 5.3 下载前端静态资源

```bash
# 创建静态资源目录
sudo mkdir -p /opt/eims/frontend/static/js
sudo mkdir -p /opt/eims/frontend/static/css

# 下载前端依赖
cd /opt/eims/frontend/static

sudo curl -o js/vue.global.js https://unpkg.com/vue@3.4.15/dist/vue.global.js
sudo curl -o js/element-plus.js https://unpkg.com/element-plus@2.5.0/dist/index.full.js
sudo curl -o js/axios.min.js https://unpkg.com/axios@1.6.5/dist/axios.min.js
sudo curl -o css/element-plus.css https://unpkg.com/element-plus@2.5.0/dist/index.css
```

---

## 六、负载均衡配置

### 6.1 F5 BIG-IP配置

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

### 6.2 深信服AD配置

```
1. 登录AD管理界面
2. 虚拟服务 → 新增
   - 虚拟IP: 192.168.1.10
   - 端口: 80
   - 协议: TCP
3. 添加真实服务器
   - 192.168.1.22:80
   - 192.168.1.23:80
4. 负载算法: 加权最小连接
5. 健康检查: HTTP GET /health
6. 会话保持: 启用 (Cookie插入)
```

### 6.3 Nginx负载均衡（备选方案）

```bash
# 安装Nginx
sudo apt install -y nginx

# 配置负载均衡
sudo tee /etc/nginx/nginx.conf << 'EOF'
upstream eims_backend {
    least_conn;
    server 192.168.1.22:80 weight=5;
    server 192.168.1.23:80 weight=5;
    keepalive 32;
}

server {
    listen 80;
    server_name _;
    
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
EOF

sudo nginx -t
sudo systemctl restart nginx
```

---

## 七、系统验证与测试

### 7.1 健康检查

```bash
# 检查数据库服务器
curl http://192.168.1.21:5432  # 应拒绝连接（正常）
sudo -u postgres psql -c "SELECT version();"

# 检查Web服务器
curl http://192.168.1.22/health
curl http://192.168.1.23/health

# 检查负载均衡
curl http://192.168.1.10/health
```

### 7.2 功能测试

```bash
# 1. 登录测试
# 浏览器访问: http://192.168.1.10
# 使用默认账号: admin / admin123

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

### 7.3 性能测试

```bash
# 安装ab工具
sudo apt install -y apache2-utils

# 压力测试
ab -n 10000 -c 100 http://192.168.1.10/api/v1/inventory/products

# 监控资源使用
top
iotop
iftop
```

---

## 八、故障排查

### 8.1 数据库连接失败

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql-15

# 检查监听配置
sudo ss -tlnp | grep 5432

# 检查防火墙
sudo ufw status

# 检查日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 8.2 Web服务启动失败

```bash
# 检查Docker状态
sudo docker ps
sudo docker logs deploy-api-1

# 检查Nginx状态
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

# 检查端口占用
sudo ss -tlnp | grep 80
```

### 8.3 负载均衡异常

```bash
# 检查后端服务
curl -v http://192.168.1.22/health
curl -v http://192.168.1.23/health

# 检查Nginx配置
sudo nginx -t
```

---

## 附录

### A. 环境变量参考

```bash
# 数据库服务器
export DB_HOST="192.168.1.21"
export DB_PASSWORD="your-secure-password"
export REDIS_PASSWORD="your-secure-password"

# Web服务器
export SECRET_KEY="$(openssl rand -base64 48)"
export DATABASE_URL="postgresql+asyncpg://inventory:${DB_PASSWORD}@192.168.1.21:5432/inventory"
export REDIS_URL="redis://:${REDIS_PASSWORD}@192.168.1.21:6379/0"
```

### B. 常用命令

```bash
# Docker操作
sudo docker ps                    # 查看运行中的容器
sudo docker logs -f <container>   # 查看容器日志
sudo docker compose restart       # 重启所有服务

# 数据库操作
sudo -u postgres psql -d inventory  # 连接数据库
sudo systemctl restart postgresql-15 # 重启PostgreSQL

# Nginx操作
sudo nginx -t                     # 测试配置
sudo systemctl reload nginx       # 重载配置
```

### C. 备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/$DATE"
mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -h 192.168.1.21 -U inventory inventory | gzip > $BACKUP_DIR/db.sql.gz

# 备份应用配置
tar czf $BACKUP_DIR/app-config.tar.gz /opt/eims/deploy/.env

echo "Backup completed: $BACKUP_DIR"
```

---

**文档结束**

如有问题，请参考GitHub仓库: https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise
