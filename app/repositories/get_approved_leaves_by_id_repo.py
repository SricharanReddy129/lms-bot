from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

# Import your model
from app.models.base import ApprovedLeaves

async def get_approved_leaves_by_id(db: AsyncSession, employee_id: Optional[int] = None):
    stmt = select(ApprovedLeaves)
    if employee_id is not None:
        stmt = stmt.where(ApprovedLeaves.employee_id == employee_id)
        
    result = await db.execute(stmt)
    return result.scalars().all()