from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import your model
from app.models.base import RejectedLeaves

async def get_rejected_leaves_by_id(db: AsyncSession, employee_id: int):
    stmt = select(RejectedLeaves).where(RejectedLeaves.employee_id == employee_id)
    result = await db.execute(stmt)
    return result.scalars().all()