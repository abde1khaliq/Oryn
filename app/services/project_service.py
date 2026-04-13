from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from uuid import UUID
from app.models.project import Project
from app.models.team import Team
from app.models.audit_log import AuditLog

async def verify_team(db: AsyncSession, tenant_id: UUID, team_id: UUID):
    result = await db.execute(select(Team).where(Team.id == team_id, Team.tenant_id == tenant_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    return team

async def create_project(db: AsyncSession, tenant_id: UUID, user_id: UUID, team: Team, form):
    new_project = Project(
        name=form.name,
        description=form.description,
        team_id=team.id,
        tenant_id=tenant_id,
        created_by=user_id
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    audit = AuditLog(
        user_id=user_id,
        action="create_project",
        resource="project",
        status="success",
        details={"project_id": str(new_project.id), "team_id": str(team.id)}
    )
    db.add(audit)
    await db.commit()

    return new_project

async def get_projects(db: AsyncSession, tenant_id: UUID, team: Team):
    result = await db.execute(select(Project).where(Project.team_id == team.id, Project.tenant_id == tenant_id))
    return result.scalars().all()

async def get_project(db: AsyncSession, tenant_id: UUID, team_id: UUID, project_id: UUID):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.team_id == team_id, Project.tenant_id == tenant_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project

async def update_project(db: AsyncSession, tenant_id: UUID, team_id: UUID, project_id: UUID, form):
    project = await get_project(db, tenant_id, team_id, project_id)
    if form.name:
        project.name = form.name
    if form.description:
        project.description = form.description
    await db.commit()
    await db.refresh(project)

    audit = AuditLog(
        user_id=project.created_by,
        action="update_project",
        resource="project",
        status="success",
        details={"project_id": str(project.id), "team_id": str(team_id)}
    )
    db.add(audit)
    await db.commit()

    return project

async def delete_project(db: AsyncSession, tenant_id: UUID, team_id: UUID, project_id: UUID):
    project = await get_project(db, tenant_id, team_id, project_id)
    await db.delete(project)
    await db.commit()

    audit = AuditLog(
        user_id=project.created_by,
        action="delete_project",
        resource="project",
        status="success",
        details={"project_id": str(project_id), "team_id": str(team_id)}
    )
    db.add(audit)
    await db.commit()

    return project
