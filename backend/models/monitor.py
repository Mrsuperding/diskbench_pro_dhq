from sqlalchemy import Column, Integer, Float, DateTime
from core.database import Base
from datetime import datetime
class Monitor(Base):
    __tablename__ = "monitor"
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    cpu = Column(Float)
    mem = Column(Float)
    disk = Column(Float)