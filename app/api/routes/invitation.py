import secrets
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.invitation import Invitation
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.schemas.invitation import InvitationForm, AcceptInvitationForm
from app.core.config import settings
from app.core.security import hash_password

router = APIRouter()


@router.post(
    '/invitations',
    summary="Create an invitation link",
    description="Generates a unique invitation token for the current tenant. Only owners can create invitations. If an invitation already exists for this tenant it will be overwritten with a new token."
)
async def create_invitation_route(
    form: InvitationForm,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role not in ['owner']:
        raise HTTPException(status_code=403, detail='Only owners can invite members.')

    token = secrets.token_urlsafe(8)

    result = await db.execute(
        select(Invitation).where(Invitation.tenant_id == user.tenant_id)
    )
    existing_invitation = result.scalar_one_or_none()

    if existing_invitation:
        existing_invitation.token = token
        existing_invitation.max_uses = form.max_uses
        existing_invitation.uses = 0
    else:
        invitation = Invitation(
            tenant_id=user.tenant_id,
            token=token,
            max_uses=form.max_uses,
            created_by=user.id
        )
        db.add(invitation)

    await db.commit()
    return {"invitation_token": f"{token}"}


@router.get(
    '/invitations/{token}',
    summary="Validate an invitation token",
    description="Checks whether an invitation token is valid and has not exceeded its maximum uses. Returns the associated tenant ID if valid. Use this before showing the registration form to the invited user."
)
async def validate_invitation_token_route(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail='Invitation link is invalid.')

    if invitation.uses >= invitation.max_uses:
        raise HTTPException(status_code=400, detail='Invitation link has reached its maximum uses.')

    return {"valid": True, "tenant_id": invitation.tenant_id}


@router.post(
    '/invitations/{token}/accept',
    summary="Accept an invitation and create an account",
    description="Registers a new member user under the tenant associated with the invitation token. The token must be valid and have remaining uses. The email must not already exist within the same workspace."
)
async def accept_invitation_route(
    form: AcceptInvitationForm,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=404, detail='Invitation link is invalid.')

    if invitation.uses >= invitation.max_uses:
        raise HTTPException(status_code=400, detail='Invitation link has reached its maximum uses.')

    existing = await db.execute(
        select(User).where(User.email == form.email, User.tenant_id == invitation.tenant_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail='This email is already in this Workspace.')

    user = User(
        email=form.email,
        username=form.username,
        password_hash=hash_password(form.password),
        role='member',
        tenant_id=invitation.tenant_id
    )
    db.add(user)
    invitation.uses += 1

    await db.commit()
    return {"message": "Account created successfully."}