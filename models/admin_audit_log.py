from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from database import Base


class AdminAuditLog(Base):
    __tablename__ = "AdminAuditLog"
    __table_args__ = {'schema': 'dbo'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    admin_user = Column(String(100), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    summary = Column(String(500), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
