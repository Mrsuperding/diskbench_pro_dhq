from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/io_test_platform"
    
    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://localhost:5173",  # 添加这行
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",  # 添加这行
    ]
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 监控配置
    MONITOR_INTERVAL: int = 5  # 监控数据收集间隔（秒）
    LOG_RETENTION_DAYS: int = 30  # 日志保留天数
    
    # 任务配置
    MAX_CONCURRENT_TASKS: int = 10
    TASK_TIMEOUT: int = 3600  # 任务超时时间（秒）
    
    class Config:
        env_file = ".env"

settings = Settings()