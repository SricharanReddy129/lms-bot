from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

# import both your models here:
from app.models.base import PendingLeaves, ApprovedLeaves, LeaveBalance

async def bulk_leave_approval(db: AsyncSession, approval_payload: list[dict]):
    """
    Phase 2: Atomic transaction for Insert, Update (Deduction), and Delete.
    Expects a payload containing the pending record, target column, and deduction amount.
    """
    approved_objects_to_insert = []
    leave_ids_to_delete = []

    for item in approval_payload:
        pending = item["pending_record"]
        leave_ids_to_delete.append(pending.sno)

        # 1. Prepare Insert
        new_approved_leave = ApprovedLeaves(
            leave_id=pending.sno,
            employee_id=pending.employee_id,
            leave_type=pending.leave_type,
            start_date=pending.start_date,
            end_date=pending.end_date
        )
        approved_objects_to_insert.append(new_approved_leave)

        # 2. Execute dynamic balance deduction
        column_name = item["target_column"]
        deduction = item["days_to_deduct"]
        emp_id = item["employee_id"]

        # Dynamically target the correct column (e.g., LeaveBalance.sick_leaves)
        balance_column = getattr(LeaveBalance, column_name)
        
        deduct_stmt = (
            update(LeaveBalance)
            .where(LeaveBalance.employee_id == emp_id)
            .values({column_name: balance_column - deduction})
        )
        await db.execute(deduct_stmt)

    # 3. Add all new approved records
    db.add_all(approved_objects_to_insert)

    # 4. Remove old pending records
    delete_stmt = delete(PendingLeaves).where(PendingLeaves.sno.in_(leave_ids_to_delete))
    await db.execute(delete_stmt)

    # 5. Commit everything atomically
    await db.commit()