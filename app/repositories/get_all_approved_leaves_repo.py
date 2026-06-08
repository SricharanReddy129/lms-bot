from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import your model
from app.models.base import ApprovedLeaves

async def get_all_approved_leaves(db: AsyncSession):
    stmt = select(ApprovedLeaves)
    result = await db.execute(stmt)
    return result.scalars().all()