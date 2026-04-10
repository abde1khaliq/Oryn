from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from uuid import UUID
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User

async def create_team(db: AsyncSession, tenant_id: UUID, name: str):
    new_team = Team(name=name, tenant_id=tenant_id)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)
    return new_team

async def get_all_teams(db: AsyncSession, tenant_id: UUID):
    result = await db.execute(select(Team).where(Team.tenant_id == tenant_id))
    return result.scalars().all()

async def get_team(db: AsyncSession, tenant_id: UUID, team_id: UUID):
    result = await db.execute(select(Team).where(Team.id == team_id, Team.tenant_id == tenant_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    return team

async def update_team(db: AsyncSession, tenant_id: UUID, team_id: UUID, name: str = None):
    team = await get_team(db, tenant_id, team_id)
    if name:
        team.name = name
    await db.commit()
    await db.refresh(team)
    return team

async def delete_team(db: AsyncSession, tenant_id: UUID, team_id: UUID):
    team = await get_team(db, tenant_id, team_id)
    await db.execute(TeamMember.__table__.delete().where(TeamMember.team_id == team_id))
    await db.delete(team)
    await db.commit()
    return team

async def add_member_to_team(db: AsyncSession, tenant_id: UUID, team_id: UUID, user_id: UUID):
    team = await get_team(db, tenant_id, team_id)
    result = await db.execute(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in this workspace.")

    existing = await db.execute(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member of this team.")

    membership = TeamMember(team_id=team_id, user_id=user_id, tenant_id=tenant_id)
    db.add(membership)
    await db.commit()
    return user, team

async def get_team_members(db: AsyncSession, tenant_id: UUID, team_id: UUID):
    team = await get_team(db, tenant_id, team_id)
    result = await db.execute(select(User).join(TeamMember, TeamMember.user_id == User.id).where(TeamMember.team_id == team_id))
    return team, result.scalars().all()

async def remove_team_member(db: AsyncSession, tenant_id: UUID, team_id: UUID, user_id: UUID):
    team = await get_team(db, tenant_id, team_id)
    result = await db.execute(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="User is not a member of this team.")
    await db.delete(membership)
    await db.commit()
    return team
