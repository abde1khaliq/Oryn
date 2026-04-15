from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.session import get_db
from app.schemas.team import TeamCreationForm, TeamUpdateForm, TeamView, AddMemberToTeamForm
from app.services.team_service import (
    create_team, get_all_teams, get_team, update_team,
    delete_team, add_member_to_team, get_team_members, remove_team_member
)
from app.services.plan_enforcement import enforce_team_limit
from app.core.limiter import limiter

router = APIRouter()

@router.post(
    "/teams", 
    summary="Create a team", 
    description="Creates a new team inside the authenticated user's workspace. Only owners can create teams. Team names must be unique within the same workspace."
)
@limiter.limit("5/minute")
async def create_team_route(request: Request, form: TeamCreationForm, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can create teams.")

    await enforce_team_limit(current_user.tenant_id, db)    
    team = await create_team(db, current_user.tenant_id, form.name)
    return {"message": "Team created successfully.", "team": {"id": team.id, "name": team.name}}

@router.get(
    "/teams", 
    summary="Get all teams", 
    description="Returns all teams belonging to the authenticated user's workspace."
)
@limiter.limit("5/minute")
async def get_all_teams_route(request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    teams = await get_all_teams(db, current_user.tenant_id)
    return {"teams": [{"id": t.id, "name": t.name, "created_at": t.created_at} for t in teams]}

@router.get(
    "/teams/{team_id}", 
    response_model=TeamView, 
    summary="Get a team", 
    description="Returns details of a specific team within the authenticated user's workspace."
)
@limiter.limit("5/minute")
async def get_team_route(request: Request, team_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_team(db, current_user.tenant_id, team_id)

@router.patch(
    "/teams/{team_id}", 
    summary="Update a team", 
    description="Updates the name of an existing team. Only owners can edit teams."
)
@limiter.limit("5/minute")
async def update_team_route(request: Request, form: TeamUpdateForm, team_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can edit teams.")
    team = await update_team(db, current_user.tenant_id, team_id, form.name)
    return {"message": "Team updated successfully.", "team": {"id": team.id, "name": team.name}}

@router.delete(
    "/teams/{team_id}", 
    summary="Delete a team", 
    description="Permanently deletes a team and removes all its members. Only owners can delete teams."
)
@limiter.limit("5/minute")
async def delete_team_route(request: Request, team_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete teams.")
    team = await delete_team(db, current_user.tenant_id, team_id)
    return {"message": f"{team.name} has been deleted."}

@router.post(
    "/teams/{team_id}/members", 
    summary="Add a member to a team", 
    description="Adds an existing workspace member to a team. Only owners can add members. The user must already belong to the same workspace."
)
@limiter.limit("5/minute")
async def add_team_member_route(request: Request, form: AddMemberToTeamForm, team_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can add members to teams.")
    user, team = await add_member_to_team(db, current_user.tenant_id, team_id, form.user_id)
    return {"message": f"{user.username} has been added to {team.name}."}

@router.get(
    "/teams/{team_id}/members", 
    summary="Get all members of a team", 
    description="Returns all members belonging to a specific team within the authenticated user's workspace."
)
@limiter.limit("5/minute")
async def get_team_members_route(request: Request, team_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    team, members = await get_team_members(db, current_user.tenant_id, team_id)
    return {"team": team.name, "members": [{"id": m.id, "username": m.username, "email": m.email, "role": m.role} for m in members]}

@router.delete(
    "/teams/{team_id}/members/{user_id}", 
    summary="Remove a member from a team", 
    description="Removes a user from a team. Only owners can remove members."
)
@limiter.limit("5/minute")
async def remove_team_member_route(request: Request, team_id: UUID, user_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can remove members from teams.")
    team = await remove_team_member(db, current_user.tenant_id, team_id, user_id)
    return {"message": "Member removed from team successfully."}
