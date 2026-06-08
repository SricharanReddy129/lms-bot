from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import PendingLeaves

async def get_all_pending_leaves(db: AsyncSession):
    stmt = select(PendingLeaves)
    result = await db.execute(stmt)
    pending_leaves = result.scalars().all()
    return pending_leaves