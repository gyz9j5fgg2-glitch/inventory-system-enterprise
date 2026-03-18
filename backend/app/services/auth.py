from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os

from app.config import settings
from app.models.user import User
from app.services.ldap_auth import ldap_service
from app.services.permissions import has_permission, get_role_permissions

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 使用HTTPS的token URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),  # 签发时间
        "iss": "eims-api"  # 签发者
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "iss": "eims-api"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def authenticate_user(db: AsyncSession, username: str, password: str):
    """
    用户认证 - 支持本地和LDAP/AD认证
    LDAP必须使用LDAPS (SSL/TLS)
    """
    # 1. 先尝试本地数据库认证
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user and user.is_active:
        # 本地密码验证
        if user.hashed_password and verify_password(password, user.hashed_password):
            return user
        
        # 本地用户但密码为空，可能是域账号
        if not user.hashed_password and ldap_service.is_enabled():
            ldap_user = ldap_service.authenticate(username, password)
            if ldap_user:
                # 更新用户信息
                user.name = ldap_user.get('name', user.name)
                user.email = ldap_user.get('email', user.email)
                await db.commit()
                return user
    
    # 2. 尝试 LDAP 域认证（用户可能不在本地数据库）
    if ldap_service.is_enabled():
        ldap_user = ldap_service.authenticate(username, password)
        if ldap_user:
            # 自动创建本地用户
            from app.models.user import User
            new_user = User(
                username=username,
                email=ldap_user.get('email', f'{username}@company.com'),
                name=ldap_user.get('name', username),
                is_active=True
            )
            # 根据AD组分配角色
            if 'Domain Admins' in ldap_user.get('groups', []):
                new_user.role = 'admin'
            elif 'Warehouse Managers' in ldap_user.get('groups', []):
                new_user.role = 'warehouse_manager'
            else:
                new_user.role = 'user'
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
    
    return None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            issuer="eims-api"  # 验证签发者
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # 检查token类型
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # TODO: 从数据库获取用户
    return {"username": username}


async def require_permission(permission: str):
    """权限检查装饰器工厂"""
    async def check_permission(current_user = Depends(get_current_user)):
        if not has_permission(current_user.get('role', 'user'), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return check_permission


async def require_admin(current_user = Depends(get_current_user)):
    """要求管理员权限"""
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def require_warehouse_manager(current_user = Depends(get_current_user)):
    """要求仓库管理员权限（管理员也可访问）"""
    if current_user.get('role') not in ['admin', 'warehouse_manager']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要仓库管理员权限"
        )
    return current_user
