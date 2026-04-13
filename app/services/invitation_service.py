import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.invitation import Invitation
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.security import hash_password

async def create_invitation(db: AsyncSession, tenant_id: str, user_id: str, max_uses: int):
    token = secrets.token_urlsafe(8)

    result = await db.execute(select(Invitation).where(Invitation.tenant_id == tenant_id))
    existing_invitation = result.scalar_one_or_none()

    if existing_invitation:
        existing_invitation.token = token
        existing_invitation.max_uses = max_uses
        existing_invitation.uses = 0
    else:
        invitation = Invitation(
            tenant_id=tenant_id,
            token=token,
            max_uses=max_uses,
            created_by=user_id
        )
        db.add(invitation)

    await db.commit()

    audit = AuditLog(
        user_id=user_id,
        action="create_invitation",
        resource="invitation",
        status="success",
        details={"tenant_id": tenant_id, "token": token}
    )
    db.add(audit)
    await db.commit()

    return token


async def validate_invitation(db: AsyncSession, token: str):
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalar_one_or_none()

    if not invitation:
        audit = AuditLog(
            user_id=None,
            action="validate_invitation",
            resource="invitation",
            status="failure",
            details={"token": token, "reason": "not_found"}
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=404, detail='Invitation link is invalid.')

    if invitation.uses >= invitation.max_uses:
        audit = AuditLog(
            user_id=None,
            action="validate_invitation",
            resource="invitation",
            status="failure",
            details={"token": token, "reason": "max_uses_reached"}
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=400, detail='Invitation link has reached its maximum uses.')

    audit = AuditLog(
        user_id=None,
        action="validate_invitation",
        resource="invitation",
        status="success",
        details={"token": token}
    )
    db.add(audit)
    await db.commit()

    return invitation


async def accept_invitation(db: AsyncSession, token: str, email: str, username: str, password: str):
    invitation = await validate_invitation(db, token)

    existing = await db.execute(
        select(User).where(User.email == email, User.tenant_id == invitation.tenant_id)
    )
    if existing.scalar_one_or_none():
        audit = AuditLog(
            user_id=None,
            action="accept_invitation",
            resource="user",
            status="failure",
            details={"email": email, "tenant_id": invitation.tenant_id, "reason": "email_exists"}
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=400, detail='This email is already in this Workspace.')

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        role='member',
        tenant_id=invitation.tenant_id
    )
    db.add(user)
    invitation.uses += 1

    await db.commit()

    audit = AuditLog(
        user_id=user.id,
        action="accept_invitation",
        resource="user",
        status="success",
        details={"email": email, "tenant_id": invitation.tenant_id}
    )
    db.add(audit)
    await db.commit()

    return user
