from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class TeamCreationForm(BaseModel):
    name: str

class TeamView(BaseModel):
    id: UUID
    name: str
    tenant_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}

class AddMemberToTeamForm(BaseModel):
    user_id: UUID

class TeamUpdateForm(BaseModel):
    name: Optional[str] = None