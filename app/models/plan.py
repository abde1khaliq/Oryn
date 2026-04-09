# models/plan.py
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.database.session import Base
import uuid

class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    features = Column(JSONB, nullable=False)
    limits = Column(JSONB, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    tenants = relationship("Tenant", back_populates="plan")