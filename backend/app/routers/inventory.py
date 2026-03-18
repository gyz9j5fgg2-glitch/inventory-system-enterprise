from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.database import get_db
from app.schemas import InventoryResponse, InventoryListResponse, ProductCreate, ProductResponse
from app.services.auth import get_current_user, require_admin

router = APIRouter()


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取货物列表"""
    # 实现查询逻辑
    return []


@router.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """创建货物（管理员）"""
    # 实现创建逻辑
    pass


@router.get("/stock", response_model=InventoryListResponse)
async def get_inventory(
    warehouse_id: Optional[int] = None,
    product_id: Optional[int] = None,
    low_stock: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """查询库存"""
    # 实现查询逻辑
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size
    }


@router.get("/stock/{product_id}")
async def get_product_stock(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取单个货物库存详情"""
    pass


@router.post("/adjust")
async def adjust_inventory(
    product_id: int,
    warehouse_id: int,
    quantity: float,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """库存调整（管理员）"""
    pass
