from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://inventory:inventory@localhost/inventory"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # LDAP
    LDAP_ENABLED: bool = False
    LDAP_SERVER: str = "ldap://localhost:389"
    LDAP_BASE_DN: str = "dc=company,dc=com"
    LDAP_USER_DN: str = "cn=admin,dc=company,dc=com"
    LDAP_PASSWORD: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # 应用
    DEBUG: bool = False
    APP_NAME: str = "企业级库存管理系统"
    VERSION: str = "2.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
