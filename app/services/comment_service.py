from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from uuid import UUID
from app.models.comment import Comment
from app.models.task import Task
from app.models.project import Project
from app.models.team import Team
from app.models.user import User

async def verify_task_chain(db: AsyncSession, tenant_id: UUID, team_id: UUID, project_id: UUID, task_id: UUID):
    team_result = await db.execute(select(Team).where(Team.id == team_id, Team.tenant_id == tenant_id))
    if not team_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found.")

    project_result = await db.execute(select(Project).where(Project.id == project_id, Project.team_id == team_id, Project.tenant_id == tenant_id))
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found.")

    task_result = await db.execute(select(Task).where(Task.id == task_id, Task.project_id == project_id, Task.tenant_id == tenant_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task

async def create_comment(db: AsyncSession, tenant_id: UUID, user_id: UUID, task: Task, body: str):
    new_comment = Comment(body=body, task_id=task.id, tenant_id=tenant_id, created_by=user_id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment

async def get_comments(db: AsyncSession, tenant_id: UUID, task: Task):
    result = await db.execute(select(Comment).where(Comment.task_id == task.id, Comment.tenant_id == tenant_id).order_by(Comment.created_at.asc()))
    return result.scalars().all()

async def update_comment(db: AsyncSession, tenant_id: UUID, task_id: UUID, comment_id: UUID, user_id: UUID, body: str):
    result = await db.execute(select(Comment).where(Comment.id == comment_id, Comment.task_id == task_id, Comment.tenant_id == tenant_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.created_by != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments.")
    comment.body = body
    await db.commit()
    await db.refresh(comment)
    return comment

async def delete_comment(db: AsyncSession, tenant_id: UUID, task_id: UUID, comment_id: UUID, user: User):
    result = await db.execute(select(Comment).where(Comment.id == comment_id, Comment.task_id == task_id, Comment.tenant_id == tenant_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.created_by != user.id and user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this comment.")
    await db.delete(comment)
    await db.commit()
    return comment
