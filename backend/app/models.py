from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    analysis_type = Column(String) # 'url', 'pcap', 'report'
    target = Column(String)
    result_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)