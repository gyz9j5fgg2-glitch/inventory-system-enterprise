from fastapi import APIRouter, Depends
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/inventory-summary")
async def get_inventory_summary(current_user = Depends(get_current_user)):
    """库存汇总报表"""
    pass


@router.get("/transaction-log")
async def get_transaction_log(current_user = Depends(get_current_user)):
    """出入库明细"""
    pass


@router.get("/requisition-stats")
async def get_requisition_stats(current_user = Depends(get_current_user)):
    """申请统计"""
    pass
