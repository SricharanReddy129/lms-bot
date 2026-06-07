from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.api.interfaces import LeaveBalanceResponse
from app.services.leave_balance_service import get_leave_balance

# ---------------------------------------------------------
# THE SECURE ZONE
# Every endpoint attached to this router automatically 
# requires a valid JWT via the dependencies list.
# ---------------------------------------------------------
router = APIRouter(
    prefix="/api/v1", 
    tags=["Leave Management"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/leaves/balance", response_model=LeaveBalanceResponse)
async def fetch_leave_balance(
    target_employee_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) 
):
    leave_record = await get_leave_balance(
        db=db, 
        requester_id=current_user["id"],
        requester_role=current_user["role"],
        target_employee_id=target_employee_id
    )
    
    return leave_record