from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.session import get_db
from app.schemas.invitation import InvitationForm, AcceptInvitationForm
from app.services.invitation_service import create_invitation, validate_invitation, accept_invitation
from app.services.plan_enforcement import enforce_member_limit

router = APIRouter()

@router.post(
    '/invitations',
    summary="Create an invitation link",
    description="Generates a unique invitation token for the current workspace. Only owners can create invitations. If an invitation already exists for this workspace it will be overwritten with a new token."
)
async def create_invitation_route(
    form: InvitationForm,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != 'owner':
        raise HTTPException(status_code=403, detail='Only owners can invite members.')

    await enforce_member_limit(current_user.tenant_id, db)

    token = await create_invitation(db, user.tenant_id, user.id, form.max_uses)
    return {"invitation_token": token}


@router.get(
    '/invitations/{token}',
    summary="Validate an invitation token",
    description="Checks whether an invitation token is valid and has not exceeded its maximum uses. Returns the associated workspace ID if valid. Use this before showing the registration form to the invited user."
)
async def validate_invitation_token_route(token: str, db: AsyncSession = Depends(get_db)):
    invitation = await validate_invitation(db, token)
    return {"valid": True, "workspace_id": invitation.tenant_id}


@router.post(
    '/invitations/{token}/accept',
    summary="Accept an invitation and create an account",
    description="Registers a new member user under the workspace associated with the invitation token. The token must be valid and have remaining uses. The email must not already exist within the same workspace."
)
async def accept_invitation_route(
    form: AcceptInvitationForm,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    user = await accept_invitation(db, token, form.email, form.username, form.password)
    return {"message": "Account created successfully."}
