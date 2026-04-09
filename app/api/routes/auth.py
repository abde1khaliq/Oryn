from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import RegistrationForm, LoginForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.auth_service import register_user, authenticate_user


router = APIRouter()

@router.post(
    "/register",
    summary="Register a new account",
    description="""
    Creates a new user and automatically creates a Workspace under the Free plan.
    This endpoint checks if the email already exists, assigns the Free plan,
    and returns the created user details.
    """
)
async def register_route(form: RegistrationForm, db: AsyncSession = Depends(get_db)):
    """
    Register a new Workspace and owner user.
    """
    user = await register_user(form, db)
    return user


@router.post(
    "/login",
    summary="Authenticate user",
    description="""
    Authenticates a user by verifying their email and password.
    Returns a JWT access token if credentials are valid.
    """
)
async def authenticate_user_route(form: LoginForm, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT access token.
    """
    access_token = await authenticate_user(form, db)
    return {"access_token": access_token}