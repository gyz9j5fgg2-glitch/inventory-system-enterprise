from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # 数据库 - 从环境变量读取
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # JWT - 从环境变量读取，生产环境必须设置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # LDAP
    LDAP_ENABLED: bool = os.getenv("LDAP_ENABLED", "false").lower() == "true"
    LDAP_SERVER: str = os.getenv("LDAP_SERVER", "ldaps://localhost:636")
    LDAP_BASE_DN: str = os.getenv("LDAP_BASE_DN", "dc=company,dc=com")
    LDAP_USER_DN: str = os.getenv("LDAP_USER_DN", "")
    LDAP_PASSWORD: str = os.getenv("LDAP_PASSWORD", "")
    
    # CORS - 严格限制来源，生产环境必须修改
    CORS_ORIGINS: List[str] = [
        "https://inventory.company.com",
        "https://admin.company.com"
    ]
    
    # 应用
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    APP_NAME: str = "企业级库存管理系统"
    VERSION: str = "2.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 生产环境安全检查
        if not self.DEBUG:
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("生产环境必须设置长度>=32的SECRET_KEY环境变量")
            if not self.DATABASE_URL:
                raise ValueError("生产环境必须设置DATABASE_URL环境变量")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("生产环境CORS不能允许*")


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
