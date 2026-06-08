from typing import List, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the repository layer execution function
from app.repositories.bulk_leave_approval_repo import bulk_leave_approval
from app.repositories.get_employee_names_by_ids_repo import get_employee_names_by_ids

async def approve_leaves(
    db: AsyncSession,
    current_user: dict,
    leave_ids: List[int]
):
    # --- 1. ROLE CHECK ---
    if current_user["role"] != "approver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to approve leaves."
        )
    
    # --- 2. BULK DATABASE TRANSACTION ---
    approved_leaves = await bulk_leave_approval(db, leave_ids)

    if not approved_leaves:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending leaves found for the provided IDs."
        )

    # --- 3. DATA HYDRATION (Employee Names) ---
    unique_employee_ids = list({leave.employee_id for leave in approved_leaves})
    
    employees = await get_employee_names_by_ids(db, employee_ids=unique_employee_ids)
    employee_name_map = {emp.employee_id: emp.employee_name for emp in employees}

    # --- 4. FORMAT FOR PYDANTIC (The Wrapped List) ---
    hydrated_receipts = []
    for leave in approved_leaves:
        # Safely extract enum string if needed
        leave_type_str = leave.leave_type.value if hasattr(leave.leave_type, 'value') else leave.leave_type
        
        hydrated_receipts.append({
            "leave_id": leave.sno,
            "employee_id": leave.employee_id,
            "employee_name": employee_name_map.get(leave.employee_id, "Unknown"),
            "leave_type": leave_type_str
        })

    # Return the dictionary that perfectly matches ApproveLeaveResponse
    return {
        "status": "success",
        "message": f"Successfully approved {len(hydrated_receipts)} leave(s).",
        "data": hydrated_receipts
    }