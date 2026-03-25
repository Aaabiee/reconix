from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from fast_api.db import Base


class RevokedToken(Base):

    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(64), nullable=True)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<RevokedToken(jti={self.jti})>"
