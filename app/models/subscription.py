from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base
import uuid

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True)
    stripe_customer_id = Column(String, nullable=False)
    stripe_subscription_id = Column(String, nullable=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    status = Column(String, nullable=False, default="free")
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())