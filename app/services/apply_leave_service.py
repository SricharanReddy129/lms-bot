from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.add_to_pending_leaves_repo import add_to_pending_leaves
from app.repositories.leave_balance_repo import get_leave_balance_by_employee_id

async def apply_for_leave(db: AsyncSession, current_user: dict, payload):
    # checking if enough leave balance or not
    # if not enough, raise HTTPException with 400 Bad Request
    leave_balance = await get_leave_balance_by_employee_id(db, current_user["id"])

    applied_leave_days = (payload.end_date - payload.start_date).days + 1
    applied_leave_type = payload.leave_type
    column_name = f"{applied_leave_type}_leaves"
    applied_leave_balance = getattr(leave_balance, column_name)
    if applied_leave_balance < applied_leave_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not enough {applied_leave_type} leave balance. You have {applied_leave_balance} days left."
        )
    
    # If balance is sufficient, proceed to apply for leave
    await add_to_pending_leaves(db, current_user["id"],
                                payload.start_date, payload.end_date, payload.leave_type, payload.reason)
    
    return {"status": "Leave application successful"}
    
