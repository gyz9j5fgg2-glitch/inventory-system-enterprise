from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # ============================================
    # 安全配置 - 生产环境必须设置
    # ============================================
    
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
    
    # LDAP - 使用LDAPS (SSL/TLS)
    LDAP_ENABLED: bool = os.getenv("LDAP_ENABLED", "false").lower() == "true"
    LDAP_SERVER: str = os.getenv("LDAP_SERVER", "ldaps://localhost:636")  # 默认使用LDAPS
    LDAP_BASE_DN: str = os.getenv("LDAP_BASE_DN", "dc=company,dc=com")
    LDAP_USER_DN: str = os.getenv("LDAP_USER_DN", "")
    LDAP_PASSWORD: str = os.getenv("LDAP_PASSWORD", "")
    
    # ============================================
    # CORS配置 - 必须是HTTPS
    # ============================================
    # 生产环境必须使用HTTPS域名
    CORS_ORIGINS: List[str] = [
        "https://inventory.company.com",
        "https://admin.company.com",
        "https://eims.company.com"
    ]
    
    # ============================================
    # 应用配置
    # ============================================
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    APP_NAME: str = "企业级库存管理系统"
    VERSION: str = "2.0.1"
    
    # ============================================
    # HTTPS配置
    # ============================================
    # SSL证书路径（可选，使用反向代理时不需要）
    SSL_CERT_PATH: str = os.getenv("SSL_CERT_PATH", "")
    SSL_KEY_PATH: str = os.getenv("SSL_KEY_PATH", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ============================================
        # 生产环境安全检查
        # ============================================
        if not self.DEBUG:
            # JWT密钥检查
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("生产环境必须设置长度>=32的SECRET_KEY环境变量")
            
            # 数据库URL检查
            if not self.DATABASE_URL:
                raise ValueError("生产环境必须设置DATABASE_URL环境变量")
            
            # CORS检查 - 不允许*
            if "*" in self.CORS_ORIGINS:
                raise ValueError("生产环境CORS不能允许*")
            
            # CORS检查 - 必须是HTTPS
            for origin in self.CORS_ORIGINS:
                if not origin.startswith("https://"):
                    raise ValueError(f"CORS配置必须使用HTTPS: {origin}")


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
