from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from fast_api.db import Base


class IdempotencyKey(Base):

    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    user_id = Column(String(64), nullable=True)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<IdempotencyKey(key={self.key}, path={self.path})>"
