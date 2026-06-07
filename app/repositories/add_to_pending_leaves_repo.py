from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import LeaveBalance
from app.models.base import PendingLeaves

async def add_to_pending_leaves(
    db: AsyncSession, 
    employee_id: int, 
    start_date, 
    end_date, 
    leave_type,
    reason: str = None
):
    new_pending_leave = PendingLeaves(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        leave_type=leave_type,
        reason=reason
    )
    db.add(new_pending_leave)
    await db.commit()

    return "Leave application added to pending leaves successfully."