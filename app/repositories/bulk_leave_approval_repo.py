from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# import both your models here:
from app.models.base import PendingLeaves, ApprovedLeaves

async def bulk_leave_approval(db: AsyncSession, leave_ids: list[int]):
    # --- 1. FETCH ---
    # First, we must grab the pending data before we delete it
    fetch_stmt = select(PendingLeaves).where(PendingLeaves.sno.in_(leave_ids))
    result = await db.execute(fetch_stmt)
    pending_records = result.scalars().all()

    # If the list of IDs doesn't match anything in the database, stop here
    if not pending_records:
        return []

    # --- 2. INSERT ---
    # Create new instances of the ApprovedLeaves model using the pending data
    approved_objects_to_insert = []
    for pending in pending_records:
        new_approved_leave = ApprovedLeaves(
            leave_id=pending.sno,             # <-- ADDED: Safely stores the original pending ID
            employee_id=pending.employee_id,
            leave_type=pending.leave_type,
            start_date=pending.start_date,
            end_date=pending.end_date
            # <-- REMOVED: reason is no longer passed here
        )
        approved_objects_to_insert.append(new_approved_leave)
    
    # Add all new records to the session in one bulk operation
    db.add_all(approved_objects_to_insert)

    # --- 3. DELETE ---
    # Remove the old records from the pending table
    delete_stmt = delete(PendingLeaves).where(PendingLeaves.sno.in_(leave_ids))
    await db.execute(delete_stmt)

    # --- 4. COMMIT ---
    # Execute the insert and delete together as one atomic transaction
    await db.commit()

    # Return the original pending records list! 
    # Your service layer will use this list to hydrate the employee names and build the API receipts.
    return pending_records