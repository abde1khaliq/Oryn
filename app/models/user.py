from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="member")
    created_at = Column(DateTime, server_default=func.now())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True)

    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])