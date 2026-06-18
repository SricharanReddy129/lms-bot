from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import PendingLeaves

async def get_pending_leaves_by_ids(db: AsyncSession, leave_ids: list[int]):
    """
    Phase 1: Read-Only fetch of pending records.
    """
    fetch_stmt = select(PendingLeaves).where(PendingLeaves.sno.in_(leave_ids))
    result = await db.execute(fetch_stmt)
    return result.scalars().all()