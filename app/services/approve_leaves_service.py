from typing import List, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the repository layer execution function
from app.repositories.bulk_leave_approval_repo import bulk_leave_approval
from app.repositories.get_employee_names_by_ids_repo import get_employee_names_by_ids
from app.repositories.get_pending_leaves_by_leave_id_repo import get_pending_leaves_by_ids

async def approve_leaves(db: AsyncSession, current_user: dict, leave_ids: List[int]):
    # --- 1. ROLE CHECK ---
    if current_user["role"] != "approver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to approve leaves."
        )
    
    # --- 2. FETCH PENDING DATA ---
    pending_records = await get_pending_leaves_by_ids(db, leave_ids)

    if not pending_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending leaves found for the provided IDs."
        )

    # --- 3. BUSINESS LOGIC (Calculate Deductions & Map Buckets) ---
    approval_payload = []
    
    # Map incoming leave types to exact database column names
    column_map = {
        "earned": "earned_leaves",
        "sick": "sick_leaves",
        "parental": "parental_leaves"
    }

    for pending in pending_records:
        # Extract clean string
        l_type = pending.leave_type.value if hasattr(pending.leave_type, 'value') else pending.leave_type
        l_type_lower = l_type.lower()
        
        # Target the correct column, default to earned_leaves if mapping fails
        target_column = column_map.get(l_type_lower, "earned_leaves")
        
        # Date math (inclusive of start and end date)
        days_to_deduct = (pending.end_date - pending.start_date).days + 1
        
        approval_payload.append({
            "pending_record": pending,
            "employee_id": pending.employee_id,
            "target_column": target_column,
            "days_to_deduct": days_to_deduct
        })

    # --- 4. EXECUTE ATOMIC TRANSACTION ---
    await bulk_leave_approval(db, approval_payload)

    # --- 5. DATA HYDRATION (Employee Names) ---
    unique_employee_ids = list({record.employee_id for record in pending_records})
    
    employees = await get_employee_names_by_ids(db, employee_ids=unique_employee_ids)
    employee_name_map = {emp.employee_id: emp.employee_name for emp in employees}

    # --- 6. FORMAT FOR PYDANTIC ---
    hydrated_receipts = []
    for pending in pending_records:
        leave_type_str = pending.leave_type.value if hasattr(pending.leave_type, 'value') else pending.leave_type
        
        hydrated_receipts.append({
            "leave_id": pending.sno,
            "employee_id": pending.employee_id,
            "employee_name": employee_name_map.get(pending.employee_id, "Unknown"),
            "leave_type": leave_type_str
        })

    return {
        "status": "success",
        "message": f"Successfully approved {len(hydrated_receipts)} leave(s).",
        "data": hydrated_receipts
    }