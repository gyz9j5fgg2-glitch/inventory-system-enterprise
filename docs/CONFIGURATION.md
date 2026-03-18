# 系统配置指南

## 环境变量说明

### 数据库配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `DATABASE_URL` | 数据库连接URL | `postgresql+asyncpg://user:pass@host/db` |
| `DB_PASSWORD` | 数据库密码 | `YourStrongPassword123` |

### JWT 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | JWT签名密钥 | 必填 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌有效期(分钟) | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌有效期(天) | 7 |

### LDAP/AD 配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `LDAP_ENABLED` | 是否启用LDAP | `true` 或 `false` |
| `LDAP_SERVER` | LDAP服务器地址 | `ldap://ad.company.com:389` |
| `LDAP_BASE_DN` | 基础DN | `dc=company,dc=com` |
| `LDAP_USER_DN` | 服务账号DN | `cn=admin,dc=company,dc=com` |
| `LDAP_PASSWORD` | 服务账号密码 | - |

### Redis 配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `REDIS_URL` | Redis连接URL | `redis://:pass@host:6379/0` |
| `CELERY_BROKER_URL` | Celery消息队列 | `redis://:pass@host:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery结果存储 | `redis://:pass@host:6379/2` |

### 应用配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `APP_NAME` | 应用名称 | `企业级库存管理系统` |

## 配置文件示例

### 开发环境 `.env`

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://inventory:inventory@localhost/inventory

# JWT
SECRET_KEY=dev-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0

# LDAP (开发环境禁用)
LDAP_ENABLED=false

# 调试
DEBUG=true
LOG_LEVEL=DEBUG
```

### 生产环境 `.env.prod`

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://inventory:StrongPassword@db-server:5432/inventory
DB_PASSWORD=StrongPassword

# JWT (使用强密钥)
SECRET_KEY=your-production-secret-key-min-32-chars-long
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://:RedisPassword@redis-server:6379/0

# LDAP (生产环境启用)
LDAP_ENABLED=true
LDAP_SERVER=ldap://ad.company.com:389
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_DN=cn=inventory-service,dc=company,dc=com
LDAP_PASSWORD=LDAPServicePassword

# Celery
CELERY_BROKER_URL=redis://:RedisPassword@redis-server:6379/1
CELERY_RESULT_BACKEND=redis://:RedisPassword@redis-server:6379/2

# 生产设置
DEBUG=false
LOG_LEVEL=WARNING
```

## Nginx 配置

### HTTP 配置

```nginx
server {
    listen 80;
    server_name inventory.company.com;
    
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

### HTTPS 配置

```nginx
server {
    listen 443 ssl http2;
    server_name inventory.company.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        root /opt/inventory-system/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
        expires 1d;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

server {
    listen 80;
    server_name inventory.company.com;
    return 301 https://$server_name$request_uri;
}
```

## 日志配置

### 日志级别

- `DEBUG` - 调试信息（开发环境）
- `INFO` - 一般信息
- `WARNING` - 警告
- `ERROR` - 错误
- `CRITICAL` - 严重错误

### 日志位置

```bash
# Docker 日志
docker-compose logs -f api

# 系统日志（如配置了文件日志）
tail -f /var/log/inventory/app.log
```
