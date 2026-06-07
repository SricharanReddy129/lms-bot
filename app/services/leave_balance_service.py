from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the repository layer execution function
from app.repositories.leave_balance_repo import get_leave_balance_by_employee_id

async def get_leave_balance(
    db: AsyncSession,
    current_user: dict,
    target_employee_id: Optional[int]
):
    if target_employee_id is None:
        target_employee_id = current_user["id"]

    elif target_employee_id != current_user["id"] and current_user["role"] != "approver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view other employees' leave balances."
        )
    
    elif target_employee_id != current_user["id"] and current_user["role"] == "approver":
        pass

    # 1. Call the database repository
    leave_record = await get_leave_balance_by_employee_id(db, employee_id=target_employee_id)

    # 2. Translate empty results into API-friendly errors
    if not leave_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No leave balance found for employee ID {target_employee_id}."
        )

    return leave_record