from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

# Import repo functions
from app.repositories.bulk_leave_rejection_repo import bulk_leave_rejection
from app.repositories.get_employee_names_by_ids_repo import get_employee_names_by_ids

async def reject_leaves_service(
    db: AsyncSession,
    current_user: dict,
    rejections_data: List[Dict[str, Any]] # Pure Python types!
):
    # --- 1. ROLE CHECK ---
    if current_user.get("role") != "approver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to reject leaves."
        )

    # --- 2. FORMAT DATA FOR REPOSITORY ---
    # Convert native dicts: [{"leave_id": 42, "reason": "Busy"}] -> {42: "Busy"}
    rejection_map = {item["leave_id"]: item["reason"] for item in rejections_data}
    
    # --- 3. BULK DATABASE TRANSACTION ---
    rejected_leaves = await bulk_leave_rejection(db, rejection_map)

    if not rejected_leaves:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending leaves found for the provided IDs."
        )

    # --- 4. DATA HYDRATION (Employee Names) ---
    unique_employee_ids = list({leave.employee_id for leave in rejected_leaves})
    
    employees = await get_employee_names_by_ids(db, employee_ids=unique_employee_ids)
    employee_name_map = {emp.employee_id: emp.employee_name for emp in employees}

    # --- 5. FORMAT FOR PYDANTIC (The Wrapped List) ---
    hydrated_receipts = []
    for leave in rejected_leaves:
        leave_type_str = leave.leave_type.value if hasattr(leave.leave_type, 'value') else leave.leave_type
        
        hydrated_receipts.append({
            "leave_id": leave.sno,
            "employee_id": leave.employee_id,
            "employee_name": employee_name_map.get(leave.employee_id, "Unknown"),
            "leave_type": leave_type_str
        })

    # Return a native dict; FastAPI will automatically validate it against RejectLeaveResponse
    return {
        "status": "success",
        "message": f"Successfully rejected {len(hydrated_receipts)} leave(s).",
        "data": hydrated_receipts
    }