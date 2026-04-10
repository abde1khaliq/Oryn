from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProjectCreationForm(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectView(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    team_id: UUID
    tenant_id: UUID
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}