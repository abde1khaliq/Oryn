from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class TaskCreationForm(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None

class TaskUpdateForm(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None

class TaskStatusUpdateForm(BaseModel):
    status: str

class TaskView(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    project_id: UUID
    tenant_id: UUID
    assigned_to: Optional[UUID]
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}