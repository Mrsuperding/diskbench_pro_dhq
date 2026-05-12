from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from core.config import settings
# 创建数据库引擎 - 使用 QueuePool 连接池支持并发
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # 基础连接数
    max_overflow=20,        # 允许超额的最大连接数
    pool_timeout=30,        # 获取连接超时时间（秒）
    pool_recycle=1800,      # 30分钟回收连接，避免 MySQL wait_timeout 超时
    pool_pre_ping=True,     # 使用前检查连接有效性
    echo=False              # 生产环境关闭 SQL 日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖注入函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()