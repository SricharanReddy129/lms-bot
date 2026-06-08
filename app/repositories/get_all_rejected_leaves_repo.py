from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import your model
from app.models.base import RejectedLeaves

async def get_all_rejected_leaves(db: AsyncSession):
    stmt = select(RejectedLeaves)
    result = await db.execute(stmt)
    return result.scalars().all()