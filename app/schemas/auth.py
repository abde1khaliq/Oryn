from pydantic import BaseModel, EmailStr

class RegistrationForm(BaseModel):
    email: EmailStr
    username: str
    company_name: str
    password: str

class LoginForm(BaseModel):
    email: EmailStr
    password: str