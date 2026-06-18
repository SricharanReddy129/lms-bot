from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import PendingLeaves

async def get_pending_leaves_by_employee_id(db: AsyncSession, employee_id: int):
    stmt = select(PendingLeaves).where(PendingLeaves.employee_id == employee_id)
    result = await db.execute(stmt)
    pending_leaves = result.scalars().all()
    return pending_leaves