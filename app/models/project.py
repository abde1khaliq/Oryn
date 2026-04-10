from sqlalchemy import String, Column, ForeignKey, func, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base
import uuid

class Project(Base):
    __tablename__ = 'projects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    team = relationship("Team", backref="projects")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        UniqueConstraint('tenant_id', 'team_id', 'name', name='uq_project_name_per_team'),
    )