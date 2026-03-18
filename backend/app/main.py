from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.database import engine, Base
from app.routers import auth, inventory, requisition, approval, reports, warehouse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表（生产环境使用 Alembic）
    async with engine.begin() as conn:
        pass
    yield
    # 关闭时清理
    await engine.dispose()


app = FastAPI(
    title="企业级库存管理系统",
    description="Enterprise Inventory Management System API",
    version="2.0.1",
    lifespan=lifespan,
    docs_url=None,  # 禁用Swagger UI（生产环境）
    redoc_url=None   # 禁用ReDoc（生产环境）
)


# 生产环境强制HTTPS重定向
if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)


# 安全中间件 - 添加安全响应头
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"
    # 防止MIME类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"
    # XSS保护
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # 强制HTTPS (HSTS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    # 内容安全策略 (CSP) - 只允许HTTPS
    response.headers["Content-Security-Policy"] = "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https:; font-src 'self' https:; img-src 'self' data: https:; connect-src 'self' https:;"
    # referrer策略
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # 权限策略
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# CORS配置 - 严格限制来源，只允许HTTPS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 限制HTTP方法
    allow_headers=["Authorization", "Content-Type"],  # 限制请求头
    expose_headers=["X-Request-ID"],
    max_age=600,  # 预检请求缓存10分钟
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
    """健康检查端点"""
    return {"status": "ok", "version": "2.0.1"}


@app.get("/")
async def root():
    return {
        "message": "企业级库存管理系统 API",
        "version": "2.0.1",
        "protocol": "HTTPS",
        "docs": None  # 生产环境不暴露文档地址
    }
