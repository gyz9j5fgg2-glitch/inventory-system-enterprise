# 企业级库存管理系统 - 安全修复说明

**修复日期**: 2024-03-18  
**修复版本**: v2.0.1-security  
**修复状态**: ✅ 已完成

---

## 已修复的高危漏洞

### ✅ 1. JWT密钥硬编码 [CVE-2022-23529]

**修复内容**:
- 移除代码中的默认密钥
- 改为从环境变量 `SECRET_KEY` 读取
- 添加启动检查，确保密钥长度>=32
- 生产环境未设置密钥时拒绝启动

**验证方式**:
```bash
# 不设置密钥时启动会报错
export SECRET_KEY=""
python -c "from app.config import settings"
# ValueError: 生产环境必须设置长度>=32的SECRET_KEY环境变量

# 设置正确密钥后正常启动
export SECRET_KEY="$(openssl rand -base64 48)"
python -c "from app.config import settings; print('OK')"
```

---

### ✅ 2. CORS配置过于宽松 [CWE-942]

**修复内容**:
- 移除通配符 `*`
- 默认只允许特定域名
- 生产环境检查不允许 `*` 和 `allow_credentials` 同时存在
- 限制HTTP方法为 GET/POST/PUT/DELETE
- 限制请求头为 Authorization/Content-Type

**配置示例**:
```python
CORS_ORIGINS = [
    "https://inventory.company.com",
    "https://admin.company.com"
]
```

---

### ✅ 3. 前端CDN无SRI校验 [CWE-830]

**修复内容**:
- 添加CSP (Content Security Policy) 头
- 前端资源改为本地托管路径
- 创建 `frontend/static/` 目录存放JS/CSS
- 移除外部CDN依赖

**文件结构**:
```
frontend/
├── index.html          # 引用本地资源
└── static/
    ├── js/
    │   ├── vue.global.js
    │   ├── element-plus.js
    │   └── axios.min.js
    └── css/
        └── element-plus.css
```

**部署时需下载资源**:
```bash
cd frontend/static

# 下载Vue.js
curl -o js/vue.global.js https://unpkg.com/vue@3.4.15/dist/vue.global.js

# 下载Element Plus
curl -o js/element-plus.js https://unpkg.com/element-plus@2.5.0/dist/index.full.js
curl -o css/element-plus.css https://unpkg.com/element-plus@2.5.0/dist/index.css

# 下载Axios
curl -o js/axios.min.js https://unpkg.com/axios@1.6.5/dist/axios.min.js
```

---

### ✅ 4. 安全响应头 [CWE-693]

**新增响应头**:
```
X-Frame-Options: DENY                    # 防止点击劫持
X-Content-Type-Options: nosniff          # 防止MIME嗅探
X-XSS-Protection: 1; mode=block          # XSS保护
Strict-Transport-Security: max-age=31536000; includeSubDomains  # HSTS
Content-Security-Policy: default-src 'self'  # CSP
Referrer-Policy: strict-origin-when-cross-origin  # Referrer策略
```

---

### ✅ 5. 登录速率限制 [CWE-770]

**修复内容**:
- 登录接口添加IP级速率限制
- 5分钟内最多5次尝试
- 超过限制封禁5分钟
- 返回429状态码

**实现方式**:
```python
# 内存存储（生产环境建议使用Redis）
login_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_TIME = 300  # 5分钟

@router.post("/login")
async def login(request: Request, ...):
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(429, "登录尝试次数过多")
```

---

### ✅ 6. API文档暴露 [CWE-1059]

**修复内容**:
- 生产环境禁用 Swagger UI (`docs_url=None`)
- 生产环境禁用 ReDoc (`redoc_url=None`)
- 可通过环境变量控制是否启用

---

## 部署前检查清单

```bash
# 1. 检查JWT密钥
export SECRET_KEY="$(openssl rand -base64 48)"
echo "JWT密钥长度: ${#SECRET_KEY}"
# 应输出: JWT密钥长度: 64

# 2. 检查数据库URL
export DATABASE_URL="postgresql+asyncpg://inventory:StrongPassword@db-server:5432/inventory"

# 3. 检查CORS配置
# 修改 backend/app/config.py 中的 CORS_ORIGINS

# 4. 下载前端静态资源
cd frontend/static/js
curl -O https://unpkg.com/vue@3.4.15/dist/vue.global.js
curl -O https://unpkg.com/element-plus@2.5.0/dist/index.full.js
curl -O https://unpkg.com/axios@1.6.5/dist/axios.min.js
cd ../css
curl -O https://unpkg.com/element-plus@2.5.0/dist/index.css

# 5. 验证配置
python -c "from app.config import settings; print('配置验证通过')"
```

---

## 环境变量模板

```bash
# 复制 backend/.env.example 为 backend/.env
# 并填写实际值

# 必填项
export SECRET_KEY="$(openssl rand -base64 48)"
export DATABASE_URL="postgresql+asyncpg://inventory:密码@主机:5432/inventory"
export REDIS_URL="redis://:密码@主机:6379/0"

# 可选项
export LDAP_ENABLED="false"
export DEBUG="false"
```

---

## 安全测试

```bash
# 1. 测试JWT密钥强度
python -c "
import os
key = os.getenv('SECRET_KEY', '')
assert len(key) >= 32, '密钥长度不足'
print('✓ JWT密钥检查通过')
"

# 2. 测试CORS配置
curl -I -H "Origin: https://evil.com" http://localhost/api/v1/auth/login
# 应返回: Access-Control-Allow-Origin: (不包含evil.com)

# 3. 测试速率限制
for i in {1..6}; do
    curl -X POST http://localhost/api/v1/auth/login -d "username=test&password=test"
done
# 第6次应返回: 429 Too Many Requests

# 4. 测试安全响应头
curl -I http://localhost/health
# 应包含: X-Frame-Options, X-Content-Type-Options等

# 5. 测试API文档禁用
curl http://localhost/docs
# 应返回: 404 Not Found
```

---

## 后续安全建议

1. **定期更新依赖**
   ```bash
   pip list --outdated
   pip install -U package-name
   ```

2. **启用HTTPS**
   - 配置SSL证书
   - 强制HTTP重定向到HTTPS
   - 启用HSTS

3. **日志审计**
   - 启用操作审计日志
   - 定期审查异常登录
   - 配置日志保留策略

4. **备份加密**
   - 数据库备份加密存储
   - 定期测试恢复流程

5. **渗透测试**
   - 部署前进行渗透测试
   - 使用OWASP ZAP扫描
   - 修复发现的问题

---

**修复完成时间**: 2024-03-18 22:10  
**建议下次审计**: 3个月后
