from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

# Import both your models here:
from app.models.base import PendingLeaves, RejectedLeaves

async def bulk_leave_rejection(db: AsyncSession, rejection_map: Dict[int, str]):
    # Extract just the IDs for the SQL query
    leave_ids = list(rejection_map.keys())

    # --- 1. FETCH ---
    fetch_stmt = select(PendingLeaves).where(PendingLeaves.sno.in_(leave_ids))
    result = await db.execute(fetch_stmt)
    pending_records = result.scalars().all()

    if not pending_records:
        return []

    # --- 2. INSERT ---
    rejected_objects_to_insert = []
    for pending in pending_records:
        # Grab the specific reason the manager provided for this exact leave_id
        approver_reason = rejection_map.get(pending.sno, "No reason provided")
        
        new_rejected_leave = RejectedLeaves(
            leave_id=pending.sno,
            employee_id=pending.employee_id,
            leave_type=pending.leave_type,
            start_date=pending.start_date,
            end_date=pending.end_date,
            applicant_reason=pending.reason,       # The original reason from the employee
            approver_reason=approver_reason        # The manager's explicit reason
        )
        rejected_objects_to_insert.append(new_rejected_leave)
    
    db.add_all(rejected_objects_to_insert)

    # --- 3. DELETE ---
    delete_stmt = delete(PendingLeaves).where(PendingLeaves.sno.in_(leave_ids))
    await db.execute(delete_stmt)

    # --- 4. COMMIT ---
    await db.commit()

    return pending_records