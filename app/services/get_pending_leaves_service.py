from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the repository layer execution function
from app.repositories.get_employee_names_by_ids_repo import get_employee_names_by_ids
from app.repositories.get_pending_leaves_by_employee_id_repo import get_pending_leaves_by_employee_id
from app.repositories.get_all_pending_leaves_repo import get_all_pending_leaves

async def get_pending_leaves(
    db: AsyncSession,
    current_user: dict,
    target_employee_id: Optional[int]
):
    pending_leaves = [] # Store the raw SQLAlchemy objects here first

    # --- 1. ROLE-BASED FETCHING ---
    if current_user["role"] == "approver":
        if target_employee_id is not None:
            pending_leaves = await get_pending_leaves_by_employee_id(db, employee_id=target_employee_id)
            if not pending_leaves:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No pending leaves found for employee ID {target_employee_id}."
                )
        else:
            pending_leaves = await get_all_pending_leaves(db)
            if not pending_leaves:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No pending leaves found for any employee."
                )
    else:
        if target_employee_id is None:
            target_employee_id = current_user["id"]
        elif target_employee_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view other employees' pending leaves."
            )
            
        pending_leaves = await get_pending_leaves_by_employee_id(db, employee_id=target_employee_id)
        if not pending_leaves:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No pending leaves found for employee ID {target_employee_id}."
            )

    # --- 2. DATA HYDRATION (Application-Level Join) ---
    
    # Extract unique employee IDs
    unique_employee_ids = list({leave.employee_id for leave in pending_leaves})

    employees = await get_employee_names_by_ids(db, employee_ids=unique_employee_ids)

    # Create a quick lookup dictionary
    employee_name_map = {emp.employee_id: emp.employee_name for emp in employees}

    # --- 3. FORMAT FOR PYDANTIC ---
    hydrated_leaves = []
    for leave in pending_leaves:
        leave_type_str = leave.leave_type.value if hasattr(leave.leave_type, 'value') else leave.leave_type
        
        hydrated_leaves.append({
            "leave_id": leave.sno,
            "employee_id": leave.employee_id,
            "employee_name": employee_name_map.get(leave.employee_id, "Unknown"),
            "leave_type": leave_type_str,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "reason": leave.reason
        })
    return hydrated_leaves