# 企业级库存管理系统 - 安全审计报告

**审计日期**: 2024-03-18  
**审计范围**: 源代码、Web平台、部署配置  
**风险等级**: 🔴 高危 | 🟡 中危 | 🟢 低危 | 🔵 信息

---

## 执行摘要

本次安全审计发现 **3个高危漏洞**、**5个中危漏洞**、**4个低危风险**，建议在生产环境部署前修复所有高危和中危漏洞。

| 风险等级 | 数量 | 状态 |
|---------|------|------|
| 🔴 高危 | 3 | 必须修复 |
| 🟡 中危 | 5 | 建议修复 |
| 🟢 低危 | 4 | 可选修复 |
| 🔵 信息 | 3 | 了解即可 |

---

## 🔴 高危漏洞 (必须修复)

### 1. JWT密钥硬编码/弱密钥 [CVE-2022-23529]

**位置**: `backend/app/config.py:15`

```python
SECRET_KEY: str = "your-secret-key-change-in-production"
```

**风险**: 
- 使用默认弱密钥，攻击者可伪造JWT令牌
- 可绕过身份验证，获取任意用户权限

**修复方案**:
```python
# 生成强密钥
import secrets
SECRET_KEY = secrets.token_urlsafe(64)

# 或从环境变量读取
SECRET_KEY: str = os.getenv('SECRET_KEY')
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters")
```

**验证命令**:
```bash
# 检查密钥强度
python -c "import os; key=os.getenv('SECRET_KEY',''); print('OK' if len(key)>=32 else 'WEAK')"
```

---

### 2. CORS配置过于宽松 [CWE-942]

**位置**: `backend/app/main.py:25-31`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 可能包含 *
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险**:
- 允许任意来源访问API
- 配合allow_credentials=true可导致会话劫持

**修复方案**:
```python
# 严格限制来源
CORS_ORIGINS: List[str] = [
    "https://inventory.company.com",
    "https://admin.company.com"
]

# 禁止通配符
if "*" in CORS_ORIGINS and allow_credentials:
    raise ValueError("CORS cannot allow * with credentials")
```

---

### 3. 前端CDN依赖无完整性校验 [CWE-830]

**位置**: `frontend/index.html:7-10`

```html
<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
<script src="https://unpkg.com/element-plus/dist/index.full.js"></script>
<script src="https://unpkg.com/axios/dist/axios.min.js"></script>
```

**风险**:
- CDN被攻击时，恶意代码直接注入
- 无SRI校验，无法检测文件篡改

**修复方案**:
```html
<!-- 使用SRI校验 -->
<script src="https://unpkg.com/vue@3.4.15/dist/vue.global.js" 
        integrity="sha384-xxxxxxxxxxxxxxxx"
        crossorigin="anonymous"></script>

<!-- 或本地托管 -->
<script src="/static/js/vue@3.4.15.global.js"></script>
```

---

## 🟡 中危漏洞 (建议修复)

### 4. 数据库连接信息明文存储 [CWE-798]

**位置**: `backend/app/config.py:9`

```python
DATABASE_URL: str = "postgresql+asyncpg://inventory:inventory@localhost/inventory"
```

**风险**:
- 密码硬编码在配置文件中
- 代码泄露即数据库泄露

**修复方案**:
```python
# 从环境变量读取
DATABASE_URL: str = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is required")

# 使用Docker Secrets或Vault
```

---

### 5. LDAP明文密码传输 [CWE-319]

**位置**: `backend/app/services/ldap_auth.py:42`

```python
conn = Connection(server, user=user_dn, password=password, auto_bind=True)
```

**风险**:
- LDAP默认使用明文传输
- 密码可被网络嗅探

**修复方案**:
```python
# 强制使用LDAPS
LDAP_SERVER: str = "ldaps://ad.company.com:636"

# 验证证书
conn = Connection(
    server, 
    user=user_dn, 
    password=password,
    auto_bind=True,
    ssl=True,
    tls=Tls(validate=ssl.CERT_REQUIRED)
)
```

---

### 6. SQL注入风险 [CWE-89]

**位置**: `backend/app/routers/warehouse.py:35`

```python
po_no = f"PO{datetime.now().strftime('%Y%m%d%H%M%S')}"
```

**风险**:
- 字符串拼接生成PO号，存在注入风险
- 需确保所有数据库操作使用参数化查询

**修复方案**:
```python
# 使用参数化查询（SQLAlchemy已处理）
# 确保所有raw SQL使用参数绑定

# 生成唯一ID使用UUID
import uuid
po_no = f"PO{uuid.uuid4().hex[:12].upper()}"
```

---

### 7. 缺少速率限制 [CWE-770]

**位置**: `backend/app/routers/auth.py:17`

```python
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
```

**风险**:
- 无登录速率限制，易受暴力破解攻击
- 无API速率限制，易受DDoS攻击

**修复方案**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    ...
```

---

### 8. 敏感信息日志泄露 [CWE-532]

**位置**: 多处API接口

**风险**:
- 可能记录密码、Token等敏感信息
- 日志文件被访问时信息泄露

**修复方案**:
```python
# 配置日志过滤器
import logging

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        record.msg = str(record.msg).replace(record.args.get('password', ''), '***')
        return True

logging.getLogger().addFilter(SensitiveDataFilter())
```

---

## 🟢 低危风险 (可选修复)

### 9. 测试账号硬编码 [CWE-798]

**位置**: `frontend/index.html:28-32`

```html
申请人: applicant / applicant123
审批人: approver / approver123
仓库管理员: warehouse / warehouse123
管理员: admin / admin123
```

**风险**:
- 测试账号信息泄露
- 生产环境未删除导致未授权访问

**修复方案**:
- 生产环境删除测试账号
- 使用环境变量控制显示

---

### 10. 缺少安全响应头 [CWE-693]

**位置**: `backend/app/main.py`

**风险**:
- 缺少X-Frame-Options、X-XSS-Protection等头
- 增加XSS和Clickjacking风险

**修复方案**:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

# 添加安全头
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

### 11. 会话管理不完善 [CWE-613]

**位置**: `backend/app/services/auth.py`

**风险**:
- Token无吊销机制
- 用户登出后Token仍有效

**修复方案**:
```python
# 使用Redis存储Token黑名单
import redis

redis_client = redis.Redis()

async def logout(token: str):
    # 将Token加入黑名单
    redis_client.setex(f"blacklist:{token}", 3600, "revoked")

async def get_current_user(token: str):
    # 检查Token是否在黑名单
    if redis_client.get(f"blacklist:{token}"):
        raise HTTPException(status_code=401, detail="Token revoked")
    ...
```

---

### 12. 依赖组件版本未锁定 [CWE-1104]

**位置**: `backend/requirements.txt`

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
```

**风险**:
- 部分依赖使用最新版本
- 可能引入未测试的安全漏洞

**修复方案**:
```bash
# 锁定所有依赖版本
pip freeze > requirements.lock

# 定期使用safety检查
pip install safety
safety check -r requirements.txt
```

---

## 🔵 信息项 (了解即可)

### 13. API文档暴露 [CWE-1059]

**位置**: `/docs` (Swagger UI)

**说明**:
- 生产环境暴露API文档可能泄露接口信息
- 建议限制访问或禁用

**修复方案**:
```python
app = FastAPI(
    docs_url=None,  # 禁用Swagger UI
    redoc_url=None,  # 禁用ReDoc
)

# 或限制IP访问
@app.middleware("http")
async def docs_access_control(request, call_next):
    if request.url.path in ["/docs", "/redoc"]:
        if request.client.host not in ["127.0.0.1", "10.0.0.0/8"]:
            raise HTTPException(status_code=403)
    return await call_next(request)
```

---

### 14. 健康检查端点 [CWE-200]

**位置**: `/health`

**说明**:
- 暴露系统运行信息
- 可能被用于信息收集

**建议**:
- 限制访问IP
- 不暴露详细版本信息

---

### 15. 调试模式风险 [CWE-489]

**位置**: `backend/app/config.py:40`

```python
DEBUG: bool = False
```

**说明**:
- 确保生产环境DEBUG=False
- 错误信息不暴露敏感信息

---

## 修复优先级建议

### 立即修复 (上线前)
1. 🔴 JWT密钥硬编码
2. 🔴 CORS配置过于宽松
3. 🔴 前端CDN无SRI

### 短期修复 (1周内)
4. 🟡 数据库连接信息明文存储
5. 🟡 LDAP明文传输
6. 🟡 缺少速率限制

### 中期修复 (1月内)
7. 🟡 SQL注入风险检查
8. 🟡 敏感信息日志过滤
9. 🟢 安全响应头
10. 🟢 会话管理完善

---

## 安全加固检查清单

```bash
# 部署前检查
□ JWT密钥长度 >= 32字符且随机生成
□ CORS不允许多个来源同时允许credentials
□ 所有CDN资源使用SRI或本地托管
□ 数据库密码从环境变量读取
□ LDAP使用LDAPS (636端口)
□ 登录接口有速率限制 (5次/分钟)
□ 生产环境禁用DEBUG模式
□ API文档限制访问或禁用
□ 启用HTTPS并配置HSTS
□ 配置安全响应头
□ 定期更新依赖包
□ 启用日志审计
□ 配置备份加密
```

---

## 安全测试建议

```bash
# 1. 依赖漏洞扫描
pip install safety bandit
safety check -r requirements.txt
bandit -r backend/

# 2. 容器镜像扫描
docker run --rm -v $(pwd):/app aquasec/trivy fs /app

# 3. 渗透测试工具
# OWASP ZAP
# Burp Suite
# Nikto

# 4. JWT安全测试
# https://jwt.io/
# 尝试修改算法为none
# 尝试暴力破解密钥
```

---

## 参考资源

- [OWASP Top 10 2021](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)

---

**报告生成时间**: 2024-03-18 22:00  
**下次审计建议**: 3个月后或重大更新后
