# 企业级库存管理系统 - Ubuntu部署指南

**适用环境**: 现有虚拟化平台 + Ubuntu 22.04 LTS

---

## 快速开始（3步部署）

### 第1步：创建Ubuntu虚拟机

在现有虚拟化平台上创建3台虚拟机：

| 虚拟机名称 | 规格 | IP地址 | 用途 |
|-----------|------|--------|------|
| eims-db | 8核/32GB/600GB | 192.168.1.21 | 数据库 |
| eims-web01 | 4核/8GB/100GB | 192.168.1.22 | Web服务1 |
| eims-web02 | 4核/8GB/100GB | 192.168.1.23 | Web服务2 |

**Ubuntu安装要点：**
- 版本：Ubuntu 22.04 LTS Server
- 分区：默认即可（或手动：/boot 1GB, / 100GB, swap 8GB）
- 网络：配置静态IP
- SSH：启用OpenSSH服务器

### 第2步：部署数据库服务器

在 **eims-db** 上执行：

```bash
# 1. 下载安装脚本
curl -fsSL https://raw.githubusercontent.com/gyz9j5fgg2-glitch/inventory-system-enterprise/main/deploy/install-db-ubuntu.sh -o install-db.sh

# 2. 执行安装
chmod +x install-db.sh
sudo ./install-db.sh

# 3. 保存密码（重要！）
cat /root/db-password.txt
```

安装完成后会显示：
- PostgreSQL密码
- Redis密码
- 连接信息

### 第3步：部署Web服务器

在 **eims-web01** 和 **eims-web02** 上分别执行：

```bash
# 1. 下载安装脚本
curl -fsSL https://raw.githubusercontent.com/gyz9j5fgg2-glitch/inventory-system-enterprise/main/deploy/install-app-ubuntu.sh -o install-app.sh

# 2. 执行安装（填入实际密码）
chmod +x install-app.sh
sudo DB_HOST=192.168.1.21 DB_PASSWORD=你的数据库密码 REDIS_PASSWORD=你的Redis密码 ./install-app.sh
```

### 第4步：配置负载均衡

在现有负载均衡设备上添加后端服务器：

```
后端服务器池:
  - 192.168.1.22:80 (eims-web01)
  - 192.168.1.23:80 (eims-web02)

健康检查:
  URL: /health
  期望响应: "ok"

会话保持:
  方式: Cookie插入
  名称: EIMS_SESSION
```

---

## 验证部署

```bash
# 检查数据库
curl http://192.168.1.22/health
curl http://192.168.1.23/health

# 访问系统
# 浏览器打开: http://<负载均衡VIP>
# 默认账号: admin / admin123
```

---

## 完整部署脚本（一键部署）

```bash
#!/bin/bash
# 在管理机上执行，自动部署所有服务器

DB_HOST="192.168.1.21"
WEB01="192.168.1.22"
WEB02="192.168.1.23"
SSH_USER="ubuntu"

echo "=== 部署数据库服务器 ==="
ssh $SSH_USER@$DB_HOST "curl -fsSL https://raw.githubusercontent.com/gyz9j5fgg2-glitch/inventory-system-enterprise/main/deploy/install-db-ubuntu.sh -o install-db.sh && chmod +x install-db.sh && sudo ./install-db.sh"

# 获取密码
DB_PASS=$(ssh $SSH_USER@$DB_HOST "sudo cat /root/db-password.txt | grep 'Database Password' | cut -d': ' -f2")
REDIS_PASS=$(ssh $SSH_USER@$DB_HOST "sudo cat /root/db-password.txt | grep 'Redis Password' | cut -d': ' -f2")

echo "=== 部署Web服务器1 ==="
ssh $SSH_USER@$WEB01 "curl -fsSL https://raw.githubusercontent.com/gyz9j5fgg2-glitch/inventory-system-enterprise/main/deploy/install-app-ubuntu.sh -o install-app.sh && chmod +x install-app.sh && sudo DB_HOST=$DB_HOST DB_PASSWORD=$DB_PASS REDIS_PASSWORD=$REDIS_PASS ./install-app.sh"

echo "=== 部署Web服务器2 ==="
ssh $WEB02 "curl -fsSL https://raw.githubusercontent.com/gyz9j5fgg2-glitch/inventory-system-enterprise/main/deploy/install-app-ubuntu.sh -o install-app.sh && chmod +x install-app.sh && sudo DB_HOST=$DB_HOST DB_PASSWORD=$DB_PASS REDIS_PASSWORD=$REDIS_PASS ./install-app.sh"

echo "=== 部署完成 ==="
echo "访问地址: http://<负载均衡VIP>"
```

---

## 常见问题

### 1. Docker安装失败

```bash
# 手动安装Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
# 重新登录生效
```

### 2. PostgreSQL连接失败

```bash
# 检查监听配置
sudo ss -tlnp | grep 5432

# 检查防火墙
sudo ufw status
sudo ufw allow 5432/tcp

# 检查pg_hba.conf
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep -v "^#" | grep -v "^$"
```

### 3. Nginx启动失败

```bash
# 检查配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 检查端口占用
sudo ss -tlnp | grep 80
```

---

**部署完成！**
