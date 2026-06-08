from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

# Import repo functions
from app.repositories.get_rejected_leaves_by_id_repo import get_rejected_leaves_by_id
from app.repositories.get_all_rejected_leaves_repo import get_all_rejected_leaves
from app.repositories.get_employee_names_by_ids_repo import get_employee_names_by_ids

async def get_rejected_leaves_service(
    db: AsyncSession,
    current_user: dict,
    target_employee_id: Optional[int]
) -> Dict[str, Any]:
    
    rejected_leaves = [] # Store the raw SQLAlchemy objects here first
    
    # Safely extract the current user's ID
    current_employee_id = current_user.get("employee_id") or current_user.get("id")

    # --- 1. ROLE-BASED FETCHING ---
    if current_user.get("role") == "approver":
        if target_employee_id is not None:
            rejected_leaves = await get_rejected_leaves_by_id(db, employee_id=target_employee_id)
            if not rejected_leaves:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No rejected leaves found for employee ID {target_employee_id}."
                )
        else:
            rejected_leaves = await get_all_rejected_leaves(db)
            if not rejected_leaves:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No rejected leaves found for any employee."
                )
    else:
        if target_employee_id is None:
            target_employee_id = current_employee_id
        elif target_employee_id != current_employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view other employees' rejected leaves."
            )
            
        rejected_leaves = await get_rejected_leaves_by_id(db, employee_id=target_employee_id)
        if not rejected_leaves:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rejected leaves found for employee ID {target_employee_id}."
            )

    # --- 2. DATA HYDRATION (Application-Level Join) ---
    unique_employee_ids = list({leave.employee_id for leave in rejected_leaves})

    employees = await get_employee_names_by_ids(db, employee_ids=unique_employee_ids)
    employee_name_map = {emp.employee_id: emp.employee_name for emp in employees}

    # --- 3. FORMAT NATIVE DICTIONARIES ---
    hydrated_leaves = []
    for leave in rejected_leaves:
        leave_type_str = leave.leave_type.value if hasattr(leave.leave_type, 'value') else leave.leave_type
        
        hydrated_leaves.append({
            "history_id": leave.sno,
            "original_leave_id": leave.leave_id,
            "employee_id": leave.employee_id,
            "employee_name": employee_name_map.get(leave.employee_id, "Unknown"),
            "leave_type": leave_type_str,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "applicant_reason": leave.applicant_reason,
            "approver_reason": leave.approver_reason
        })

    # --- 4. RETURN TO GATEWAY ---
    return {
        "status": "success",
        "message": f"Retrieved {len(hydrated_leaves)} rejected leave record(s).",
        "data": hydrated_leaves
    }