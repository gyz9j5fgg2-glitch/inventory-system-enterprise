# HTTPS强制版部署指南

**版本**: v2.0.1-https  
**更新日期**: 2024-03-18  
**重要**: 本版本强制使用HTTPS，不支持HTTP访问

---

## 主要变更

1. **强制HTTPS**: 生产环境自动重定向HTTP到HTTPS
2. **安全头增强**: HSTS、CSP等安全头
3. **HTTPS检测**: 前端检测并警告非HTTPS访问
4. **LDAPS支持**: LDAP必须使用SSL/TLS (636端口)
5. **CORS限制**: 只允许HTTPS域名

---

## Nginx HTTPS配置示例

```nginx
server {
    listen 80;
    server_name inventory.company.com;
    # 强制重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name inventory.company.com;
    
    # SSL证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # SSL优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 负载均衡器HTTPS配置

### F5 BIG-IP

```tcl
# SSL Profile配置
ltm profile client-ssl https-profile {
    cert /Common/cert.pem
    key /Common/key.pem
    defaults-from /Common/clientssl
}

# Virtual Server配置
ltm virtual eims-https {
    destination 192.168.1.10:443
    ip-protocol tcp
    profiles {
        /Common/tcp { }
        /Common/https-profile { }
    }
    pool eims-pool
}

# HTTP重定向
ltm virtual eims-http {
    destination 192.168.1.10:80
    ip-protocol tcp
    rules {
        /Common/http-to-https
    }
}
```

### 深信服AD

```
1. SSL卸载配置
   - 导入SSL证书
   - 启用HTTPS服务
   
2. HTTP重定向
   - 策略 → 重定向
   - HTTP → HTTPS
   
3. 后端服务器
   - 协议: HTTP
   - 端口: 80
   - X-Forwarded-Proto: https
```

---

## 环境变量配置

```bash
# 必须设置HTTPS域名
export CORS_ORIGINS="https://inventory.company.com,https://admin.company.com"

# JWT密钥
export SECRET_KEY="$(openssl rand -base64 48)"

# 数据库（保持原有配置）
export DATABASE_URL="postgresql+asyncpg://inventory:password@db:5432/inventory"

# LDAP必须使用LDAPS
export LDAP_SERVER="ldaps://ad.company.com:636"
```

---

## 验证HTTPS配置

```bash
# 1. 检查HTTPS重定向
curl -I http://inventory.company.com
# 应返回: 301 Moved Permanently -> https://

# 2. 检查HTTPS访问
curl -I https://inventory.company.com
# 应返回: 200 OK

# 3. 检查HSTS头
curl -I https://inventory.company.com | grep Strict-Transport-Security

# 4. 检查CSP头
curl -I https://inventory.company.com | grep Content-Security-Policy

# 5. SSL证书检查
openssl s_client -connect inventory.company.com:443 -servername inventory.company.com
```

---

## 故障排查

### 问题1: 前端显示"请使用HTTPS访问"

**原因**: 直接访问HTTP或负载均衡器未正确转发协议

**解决**:
```nginx
# 在Nginx中添加
proxy_set_header X-Forwarded-Proto $scheme;
```

### 问题2: CORS错误

**原因**: CORS配置使用HTTP而非HTTPS

**解决**:
```bash
# 确保环境变量使用HTTPS
export CORS_ORIGINS="https://inventory.company.com"
```

### 问题3: LDAP连接失败

**原因**: 使用LDAP而非LDAPS

**解决**:
```bash
# 必须使用636端口和ldaps://
export LDAP_SERVER="ldaps://ad.company.com:636"
```

---

**重要提示**: 本版本强制HTTPS，请确保所有基础设施（负载均衡、反向代理）正确配置SSL/TLS。
