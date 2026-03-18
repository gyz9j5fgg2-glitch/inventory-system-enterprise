from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, inventory, requisition, approval, reports, warehouse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表（生产环境使用 Alembic）
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        pass
    yield
    # 关闭时清理
    await engine.dispose()


app = FastAPI(
    title="企业级库存管理系统",
    description="Enterprise Inventory Management System API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
async def root():
    return {
        "message": "企业级库存管理系统 API",
        "docs": "/docs",
        "version": "2.0.0"
    }
