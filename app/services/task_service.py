from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from uuid import UUID
from app.models.task import Task
from app.models.project import Project
from app.models.team import Team
from app.models.user import User
from app.models.audit_log import AuditLog

VALID_STATUSES = ["todo", "in_progress", "in_review", "done"]

async def verify_project_chain(db: AsyncSession, tenant_id: UUID, team_id: UUID, project_id: UUID):
    team_result = await db.execute(select(Team).where(Team.id == team_id, Team.tenant_id == tenant_id))
    if not team_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found.")

    project_result = await db.execute(select(Project).where(Project.id == project_id, Project.team_id == team_id, Project.tenant_id == tenant_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project

async def create_task(db: AsyncSession, tenant_id: UUID, user_id: UUID, project: Project, form):
    if form.assigned_to:
        assignee_result = await db.execute(select(User).where(User.id == form.assigned_to, User.tenant_id == tenant_id))
        if not assignee_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Assigned user not found in this workspace.")

    new_task = Task(
        title=form.title,
        description=form.description,
        assigned_to=form.assigned_to,
        project_id=project.id,
        tenant_id=tenant_id,
        created_by=user_id,
        status="todo"
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    audit = AuditLog(
        user_id=user_id,
        action="create_task",
        resource="task",
        status="success",
        details={"task_id": str(new_task.id), "project_id": str(project.id)}
    )
    db.add(audit)
    await db.commit()

    return new_task

async def get_tasks(db: AsyncSession, tenant_id: UUID, project: Project):
    result = await db.execute(select(Task).where(Task.project_id == project.id, Task.tenant_id == tenant_id))
    return result.scalars().all()

async def get_task(db: AsyncSession, tenant_id: UUID, project_id: UUID, task_id: UUID):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.project_id == project_id, Task.tenant_id == tenant_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task

async def update_task(db: AsyncSession, tenant_id: UUID, project_id: UUID, task_id: UUID, form, current_user: User):
    task = await get_task(db, tenant_id, project_id, task_id)
    if form.assigned_to:
        assignee_result = await db.execute(select(User).where(User.id == form.assigned_to, User.tenant_id == tenant_id))
        if not assignee_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Assigned user not found in this workspace.")
    if form.title:
        task.title = form.title
    if form.description:
        task.description = form.description
    if form.assigned_to:
        task.assigned_to = form.assigned_to
    await db.commit()
    await db.refresh(task)

    audit = AuditLog(
        user_id=current_user.id,
        action="update_task",
        resource="task",
        status="success",
        details={"task_id": str(task.id), "project_id": str(project_id)}
    )
    db.add(audit)
    await db.commit()

    return task

async def update_task_status(db: AsyncSession, tenant_id: UUID, project_id: UUID, task_id: UUID, status: str):
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid options are: {', '.join(VALID_STATUSES)}")
    task = await get_task(db, tenant_id, project_id, task_id)
    task.status = status
    await db.commit()

    audit = AuditLog(
        user_id=task.created_by,
        action="update_task_status",
        resource="task",
        status="success",
        details={"task_id": str(task.id), "new_status": status}
    )
    db.add(audit)
    await db.commit()

    return task

async def delete_task(db: AsyncSession, tenant_id: UUID, project_id: UUID, task_id: UUID, current_user: User):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can delete tasks.")
    task = await get_task(db, tenant_id, project_id, task_id)
    await db.delete(task)
    await db.commit()

    audit = AuditLog(
        user_id=current_user.id,
        action="delete_task",
        resource="task",
        status="success",
        details={"task_id": str(task_id), "project_id": str(project_id)}
    )
    db.add(audit)
    await db.commit()

    return task
