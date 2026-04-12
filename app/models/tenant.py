# models/tenant.py
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base
import uuid

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    plan = relationship("Plan", back_populates="tenants")
    owner = relationship("User", foreign_keys=[owner_id])
    users = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")

    stripe_customer_id = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)