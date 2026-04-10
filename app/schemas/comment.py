from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class CommentCreationForm(BaseModel):
    body: str

class CommentUpdateForm(BaseModel):
    body: str

class CommentView(BaseModel):
    id: UUID
    body: str
    task_id: UUID
    created_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}