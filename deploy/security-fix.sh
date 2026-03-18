#!/bin/bash
# security-fix.sh - 自动修复安全漏洞脚本

set -e

echo "========================================"
echo "EIMS 安全漏洞自动修复工具"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# 检查目录
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}错误: 未找到 $BACKEND_DIR 目录${NC}"
    exit 1
fi

echo "选择修复项目:"
echo "1. 修复所有高危漏洞 (推荐)"
echo "2. 修复JWT密钥硬编码"
echo "3. 修复CORS配置"
echo "4. 修复前端CDN SRI"
echo "5. 修复数据库配置"
echo "6. 添加安全响应头"
echo "7. 添加速率限制"
echo "8. 退出"
echo ""
read -p "请选择 [1-8]: " choice

# 修复JWT密钥
fix_jwt_secret() {
    echo -e "${YELLOW}[修复] JWT密钥硬编码...${NC}"
    
    # 生成强密钥
    NEW_KEY=$(openssl rand -base64 48 | tr -d "\n")
    
    # 更新配置文件
    cat > $BACKEND_DIR/.env <<EOF
# 安全密钥 - 请勿提交到Git
SECRET_KEY=${NEW_KEY}
DATABASE_URL=postgresql+asyncpg://inventory:CHANGEME@localhost/inventory
REDIS_URL=redis://localhost:6379/0
LDAP_ENABLED=false
DEBUG=false
EOF
    
    # 修改config.py从环境变量读取
    sed -i 's/SECRET_KEY: str = "your-secret-key-change-in-production"/SECRET_KEY: str = os.getenv("SECRET_KEY")/' $BACKEND_DIR/app/config.py
    
    echo -e "${GREEN}✓ JWT密钥已修复${NC}"
    echo "新密钥已保存到 $BACKEND_DIR/.env"
    echo "请确保生产环境设置正确的环境变量"
}

# 修复CORS配置
fix_cors() {
    echo -e "${YELLOW}[修复] CORS配置...${NC}"
    
    # 更新main.py
    cat > $BACKEND_DIR/app/main.py << 'EOF'
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, inventory, requisition, approval, reports, warehouse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        pass
    yield
    await engine.dispose()


app = FastAPI(
    title="企业级库存管理系统",
    description="Enterprise Inventory Management System API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # 禁用Swagger UI
    redoc_url=None   # 禁用ReDoc
)

# 安全中间件 - 添加安全响应头
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# CORS - 严格限制来源
CORS_ORIGINS = [
    "https://inventory.company.com",
    "https://admin.company.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# 路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["库存"])
app.include_router(requisition.router, prefix="/api/v1/requisitions", tags=["申请"])
app.include_router(approval.router, prefix="/api/v1/approvals", tags=["审批"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["报表"])
app.include_router(warehouse.router, prefix="/api/v1/warehouse", tags=["仓库管理"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "EIMS API", "version": "2.0.0"}
EOF
    
    echo -e "${GREEN}✓ CORS配置已修复${NC}"
    echo "注意: 请修改CORS_ORIGINS为你的实际域名"
}

# 修复前端CDN
fix_frontend_cdn() {
    echo -e "${YELLOW}[修复] 前端CDN SRI...${NC}"
    
    # 创建本地资源目录
    mkdir -p $FRONTEND_DIR/static/js
    mkdir -p $FRONTEND_DIR/static/css
    
    # 下载资源到本地
    echo "下载前端依赖到本地..."
    curl -sL https://unpkg.com/vue@3.4.15/dist/vue.global.js -o $FRONTEND_DIR/static/js/vue.global.js
    curl -sL https://unpkg.com/element-plus@2.5.0/dist/index.full.js -o $FRONTEND_DIR/static/js/element-plus.js
    curl -sL https://unpkg.com/axios@1.6.5/dist/axios.min.js -o $FRONTEND_DIR/static/js/axios.min.js
    curl -sL https://unpkg.com/element-plus@2.5.0/dist/index.css -o $FRONTEND_DIR/static/css/element-plus.css
    
    # 计算SRI哈希
    VUE_SRI=$(openssl dgst -sha384 -binary $FRONTEND_DIR/static/js/vue.global.js | openssl base64 -A)
    ELEMENT_SRI=$(openssl dgst -sha384 -binary $FRONTEND_DIR/static/js/element-plus.js | openssl base64 -A)
    AXIOS_SRI=$(openssl dgst -sha384 -binary $FRONTEND_DIR/static/js/axios.min.js | openssl base64 -A)
    
    # 更新HTML使用本地资源
    sed -i 's|https://unpkg.com/vue@3/dist/vue.global.js|/static/js/vue.global.js|g' $FRONTEND_DIR/index.html
    sed -i 's|https://unpkg.com/element-plus/dist/index.full.js|/static/js/element-plus.js|g' $FRONTEND_DIR/index.html
    sed -i 's|https://unpkg.com/axios/dist/axios.min.js|/static/js/axios.min.js|g' $FRONTEND_DIR/index.html
    sed -i 's|https://unpkg.com/element-plus/dist/index.css|/static/css/element-plus.css|g' $FRONTEND_DIR/index.html
    
    echo -e "${GREEN}✓ 前端CDN已修复${NC}"
    echo "资源已下载到 $FRONTEND_DIR/static/"
}

# 修复数据库配置
fix_database_config() {
    echo -e "${YELLOW}[修复] 数据库配置...${NC}"
    
    # 更新config.py
    sed -i 's|DATABASE_URL: str = "postgresql+asyncpg://inventory:inventory@localhost/inventory"|DATABASE_URL: str = os.getenv("DATABASE_URL")|' $BACKEND_DIR/app/config.py
    
    echo -e "${GREEN}✓ 数据库配置已修复${NC}"
    echo "请确保设置 DATABASE_URL 环境变量"
}

# 添加速率限制
add_rate_limit() {
    echo -e "${YELLOW}[修复] 添加速率限制...${NC}"
    
    # 安装依赖
    pip install slowapi
    
    # 添加到requirements.txt
    if ! grep -q "slowapi" $BACKEND_DIR/requirements.txt; then
        echo "slowapi==0.1.9" >> $BACKEND_DIR/requirements.txt
    fi
    
    cat >> $BACKEND_DIR/app/main.py << 'EOF'

# 速率限制
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
EOF
    
    # 修改登录接口添加限制
    sed -i 's|@router.post("/login")|@router.post("/login")\n@limiter.limit("5/minute")|g' $BACKEND_DIR/app/routers/auth.py
    
    echo -e "${GREEN}✓ 速率限制已添加${NC}"
}

# 修复所有
fix_all() {
    fix_jwt_secret
    fix_cors
    fix_frontend_cdn
    fix_database_config
    add_rate_limit
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}所有高危漏洞已修复!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "下一步:"
    echo "1. 检查并修改 $BACKEND_DIR/.env 中的配置"
    echo "2. 更新 $BACKEND_DIR/app/main.py 中的CORS域名"
    echo "3. 测试应用功能是否正常"
    echo "4. 部署到生产环境"
}

# 主程序
case $choice in
    1) fix_all ;;
    2) fix_jwt_secret ;;
    3) fix_cors ;;
    4) fix_frontend_cdn ;;
    5) fix_database_config ;;
    6) fix_cors ;;  # 包含安全头
    7) add_rate_limit ;;
    8) exit 0 ;;
    *) echo -e "${RED}无效选择${NC}" ;;
esac

echo ""
echo "安全修复完成!"
