# -*- coding: utf-8 -*-
"""
纯测试 MySQL 连通性
用法：
    python test_mysql.py
返回：
    ✅  All green!  表示账号、密码、库、建表全部通过
    ❌  具体异常信息
"""
from sqlalchemy import create_engine, text, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
# 1. 改成你的真实连接串
URL = "mysql+pymysql://root:123456@127.0.0.1:3306/io_test_platform?charset=utf8mb4"

engine = create_engine(URL, pool_pre_ping=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# 2. 测试点
def test_connect():
    with engine.connect() as conn:
        rs = conn.execute(text("SELECT 1"))
        assert rs.scalar() == 1
        print("✅ 连接成功")

def test_create_table():
    class Demo(Base):
        __tablename__ = "demo_test"
        id = Column(Integer, primary_key=True)
        name = String(32)

    Base.metadata.create_all(bind=engine)
    print("✅ 建表成功")

def test_insert_query():
    from sqlalchemy import Column, Integer, String
    db = SessionLocal()
    try:
        db.execute(text("INSERT INTO demo_test(name) VALUES('hello')"))
        db.commit()
        name = db.execute(text("SELECT name FROM demo_test LIMIT 1")).scalar()
        assert name == "hello"
        print("✅ 插入/查询成功")
    finally:
        db.close()

def test_cleanup():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS demo_test"))
        print("✅ 清理完成")

# 3. 主流程
if __name__ == "__main__":
    try:
        test_connect()
        test_create_table()
        test_insert_query()
        test_cleanup()
        print("\n🎉 All green! MySQL 完全就绪～")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        print("请检查密码、库名、权限或网络！")