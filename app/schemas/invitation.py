from typing import Optional
from pydantic import BaseModel, EmailStr

class InvitationForm(BaseModel):
    max_uses: Optional[int] = 5

class AcceptInvitationForm(BaseModel):
    email: EmailStr
    username: str
    password: str