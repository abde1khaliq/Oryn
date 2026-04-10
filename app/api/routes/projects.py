from fastapi import APIRouter, Depends, HTTPException
from app.schemas.project import ProjectCreationForm, ProjectUpdateForm, ProjectView
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.project import Project
from app.models.team import Team
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

router = APIRouter(prefix="/teams/{team_id}/projects")


async def verify_team(team_id: UUID, current_user: User, db: AsyncSession) -> Team:
    """Reusable helper — verifies the team exists and belongs to the current user's workspace."""
    team_result = await db.execute(
        select(Team).where(
            Team.id == team_id,
            Team.tenant_id == current_user.tenant_id
        )
    )
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    return team


@router.post(
    "",
    summary="Create a project",
    description="Creates a new project inside a specific team. Only owners and admins can create projects."
)
async def create_project_route(
    form: ProjectCreationForm,
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can create projects.")

    team = await verify_team(team_id, current_user, db)

    new_project = Project(
        name=form.name,
        description=form.description,
        team_id=team.id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return {
        "message": "Project created successfully.",
        "project": {"id": new_project.id, "name": new_project.name}
    }


@router.get(
    "",
    summary="Get all projects in a team",
    description="Returns all projects belonging to a specific team within the authenticated user's workspace."
)
async def get_team_projects_route(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    team = await verify_team(team_id, current_user, db)

    query_result = await db.execute(
        select(Project).where(
            Project.team_id == team.id,
            Project.tenant_id == current_user.tenant_id
        )
    )
    projects = query_result.scalars().all()

    return {
        "team": team.name,
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at
            }
            for project in projects
        ]
    }


@router.get(
    "/{project_id}",
    response_model=ProjectView,
    summary="Get a project",
    description="Returns details of a specific project inside a team."
)
async def get_project_route(
    team_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_team(team_id, current_user, db)

    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.team_id == team_id,
            Project.tenant_id == current_user.tenant_id
        )
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    return project


@router.patch(
    "/{project_id}",
    summary="Update a project",
    description="Updates a project's name or description. Only owners and admins can edit projects."
)
async def update_project_route(
    form: ProjectUpdateForm,
    team_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can edit projects.")

    await verify_team(team_id, current_user, db)

    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.team_id == team_id,
            Project.tenant_id == current_user.tenant_id
        )
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if form.name:
        project.name = form.name
    if form.description:
        project.description = form.description

    await db.commit()
    await db.refresh(project)

    return {
        "message": "Project updated successfully.",
        "project": {"id": project.id, "name": project.name, "description": project.description}
    }


@router.delete(
    "/{project_id}",
    summary="Delete a project",
    description="Permanently deletes a project and all its tasks. Only owners can delete projects."
)
async def delete_project_route(
    team_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete projects.")

    await verify_team(team_id, current_user, db)

    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.team_id == team_id,
            Project.tenant_id == current_user.tenant_id
        )
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    await db.delete(project)
    await db.commit()

    return {"message": f"{project.name} has been deleted."}