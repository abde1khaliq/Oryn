from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.session import get_db
from app.schemas.project import ProjectCreationForm, ProjectUpdateForm, ProjectView
from app.services.plan_enforcement import enforce_project_limit
from app.core.limiter import limiter
from app.services.project_service import (
    verify_team, create_project, get_projects,
    get_project, update_project, delete_project
)

router = APIRouter(prefix="/teams/{team_id}/projects")

@router.post(
    "", 
    summary="Create a project", 
    description="Creates a new project inside a specific team. Only owners and admins can create projects."
)
@limiter.limit("5/minute")
async def create_project_route(
    request: Request,
    form: ProjectCreationForm, 
    team_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can create projects.")

    await enforce_project_limit(current_user.tenant_id, db)
    team = await verify_team(db, current_user.tenant_id, team_id)
    project = await create_project(db, current_user.tenant_id, current_user.id, team, form)
    return {"message": "Project created successfully.", "project": {"id": project.id, "name": project.name}}

@router.get(
    "", 
    summary="Get all projects in a team", 
    description="Returns all projects belonging to a specific team within the authenticated user's workspace."
)
@limiter.limit("5/minute")
async def get_team_projects_route(
    request: Request,
    team_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    team = await verify_team(db, current_user.tenant_id, team_id)
    projects = await get_projects(db, current_user.tenant_id, team)
    return {
        "team": team.name, 
        "projects": [
            {
                "id": p.id, 
                "name": p.name, 
                "description": p.description, 
                "created_at": p.created_at
            } for p in projects
            ]
        }

@router.get(
    "/{project_id}", 
    response_model=ProjectView, 
    summary="Get a project", 
    description="Returns details of a specific project inside a team."
)
@limiter.limit("5/minute")
async def get_project_route(
    request: Request,
    team_id: UUID, 
    project_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    await verify_team(db, current_user.tenant_id, team_id)
    return await get_project(db, current_user.tenant_id, team_id, project_id)

@router.patch(
    "/{project_id}", 
    summary="Update a project", 
    description="Updates a project's name or description. Only owners and admins can edit projects."
)
@limiter.limit("5/minute")
async def update_project_route(
    request: Request,
    form: ProjectUpdateForm, 
    team_id: UUID, 
    project_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can edit projects.")
    await verify_team(db, current_user.tenant_id, team_id)
    project = await update_project(db, current_user.tenant_id, team_id, project_id, form)
    return {"message": "Project updated successfully.", "project": {"id": project.id, "name": project.name, "description": project.description}}

@router.delete(
    "/{project_id}", 
    summary="Delete a project", 
    description="Permanently deletes a project and all its tasks. Only owners can delete projects."
)
@limiter.limit("5/minute")
async def delete_project_route(
    request: Request,
    team_id: UUID, 
    project_id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete projects.")
    await verify_team(db, current_user.tenant_id, team_id)
    project = await delete_project(db, current_user.tenant_id, team_id, project_id)
    return {"message": f"{project.name} has been deleted."}
