from typing import Optional
from pydantic import BaseModel

class InvitationForm(BaseModel):
    max_uses: Optional[int] = 5
