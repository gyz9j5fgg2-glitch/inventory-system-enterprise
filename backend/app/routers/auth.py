from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import time

from app.database import get_db
from app.schemas import LoginRequest, TokenResponse, UserResponse
from app.services.auth import (
    authenticate_user, 
    create_access_token, 
    create_refresh_token,
    get_current_user
)
from app.config import settings

router = APIRouter()
# 使用HTTPS的token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="https://localhost/api/v1/auth/login")

# 简单的速率限制存储（生产环境建议使用Redis）
login_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_TIME = 300  # 5分钟


def check_rate_limit(ip: str) -> bool:
    """检查登录速率限制"""
    now = time.time()
    if ip in login_attempts:
        attempts, block_time = login_attempts[ip]
        if block_time and now < block_time:
            return False  # 仍在封禁期
        if block_time and now >= block_time:
            # 解封
            login_attempts[ip] = (0, None)
    return True


def record_failed_attempt(ip: str):
    """记录失败尝试"""
    now = time.time()
    if ip not in login_attempts:
        login_attempts[ip] = (1, None)
    else:
        attempts, _ = login_attempts[ip]
        attempts += 1
        if attempts >= MAX_ATTEMPTS:
            # 封禁5分钟
            login_attempts[ip] = (attempts, now + BLOCK_TIME)
        else:
            login_attempts[ip] = (attempts, None)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录 - 带速率限制
    生产环境必须使用HTTPS
    """
    # 检查是否使用HTTPS
    if not settings.DEBUG:
        if request.url.scheme != "https":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="必须使用HTTPS进行身份验证"
            )
    
    client_ip = request.client.host
    
    # 检查速率限制
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试次数过多，请5分钟后重试"
        )
    
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 登录成功，清除失败记录
    if client_ip in login_attempts:
        del login_attempts[client_ip]
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """刷新访问令牌"""
    # 实现刷新逻辑
    pass


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.post("/logout")
async def logout():
    """退出登录（客户端删除token）"""
    # TODO: 将Token加入黑名单（使用Redis）
    return {"message": "已退出登录"}
