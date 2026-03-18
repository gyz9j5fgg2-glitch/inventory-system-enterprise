from fastapi import APIRouter, Depends
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_requisitions(current_user = Depends(get_current_user)):
    """获取申请列表"""
    pass


@router.post("/")
async def create_requisition(current_user = Depends(get_current_user)):
    """创建申请"""
    pass


@router.get("/{req_id}")
async def get_requisition(req_id: int, current_user = Depends(get_current_user)):
    """获取申请详情"""
    pass


@router.put("/{req_id}/submit")
async def submit_requisition(req_id: int, current_user = Depends(get_current_user)):
    """提交申请"""
    pass


@router.delete("/{req_id}")
async def cancel_requisition(req_id: int, current_user = Depends(get_current_user)):
    """取消申请"""
    pass
