from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class TenantBase(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    owner_id: Optional[UUID]

    class ConfigDict:
        from_attributes = True

class PlanView(BaseModel):
    id: UUID
    name: str
    description: Optional[str]

    class ConfigDict:
        from_attributes = True

class TenantDetailView(BaseModel):
    tenant: TenantBase
    plan: PlanView
    members: int
    teams: int
    projects: int

    class ConfigDict:
        from_attributes = True
