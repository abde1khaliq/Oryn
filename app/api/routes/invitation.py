import secrets
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.invitation import Invitation
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.schemas.invitation import InvitationForm
from app.core.config import settings

router = APIRouter()

@router.post('/invitations')
async def create_invitation_route(
    form: InvitationForm,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role not in ['owner']:
        raise HTTPException(status_code=403, detail='Only owners can invite members.')

    token = secrets.token_urlsafe(8)

    # check if an invitation already exists for this tenant
    result = await db.execute(
        select(Invitation).where(Invitation.tenant_id == user.tenant_id)
    )
    existing_invitation = result.scalar_one_or_none()

    if existing_invitation:
        # overwrite the existing one
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
    return {"invite_url": f"{settings.backend_url}invitations/{token}"}