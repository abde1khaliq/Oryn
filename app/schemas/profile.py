from typing import Optional
from pydantic import BaseModel

class UpdateProfileForm(BaseModel):
    username: Optional[str] = None