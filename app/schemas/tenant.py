from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class TenantView(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    plan_id: UUID
    owner_id: Optional[UUID]

    class Config:
        from_attribute = True
