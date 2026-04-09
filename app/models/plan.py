from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.database.session import Base
import uuid

class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)      # "Free", "Pro", "Enterprise"
    price = Column(Integer, nullable=False)    # in cents — 4900 = $49/month
    features = Column(JSONB, nullable=False)   # what's unlocked
    limits = Column(JSONB, nullable=False)     # usage caps
    created_at = Column(DateTime, server_default=func.now())

    tenants = relationship("Tenant", back_populates="plan")