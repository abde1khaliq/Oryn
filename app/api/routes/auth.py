from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import RegistrationForm, LoginForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.auth_service import register_user, authenticate_user


router = APIRouter()

@router.post("/register")
async def register_route(form: RegistrationForm, db: AsyncSession = Depends(get_db)):
    user = await register_user(form, db)
    return {"message": "Account created successfully."}


@router.post("/login")
async def authenticate_user_route(form: LoginForm, db: AsyncSession = Depends(get_db)):
    access_token = await authenticate_user(form, db)
    return {"access_token": access_token}
