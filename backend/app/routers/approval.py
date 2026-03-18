from fastapi import APIRouter, Depends, Query
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/pending")
async def get_pending_approvals(
    current_user = Depends(get_current_user)
):
    """获取待我审批的任务"""
    pass


@router.post("/{task_id}/action")
async def process_approval(
    task_id: int,
    action: str,
    comment: str = None,
    current_user = Depends(get_current_user)
):
    """处理审批任务"""
    pass


@router.get("/history")
async def get_approval_history(
    current_user = Depends(get_current_user)
):
    """获取审批历史"""
    pass
