from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="member")
    created_at = Column(DateTime, server_default=func.now())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=True)

    tenant = relationship("Tenant", back_populates="owner")