from pydantic import BaseModel, EmailStr

class RegisterationForm(BaseModel):
    email: EmailStr
    username: str
    company_name: str
    password: str