from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.api.interfaces import LeaveBalanceResponse, LeaveBalanceInput
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
    payload: LeaveBalanceInput = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) 
):
    # Unpack the Pydantic input and current user dictionary into pure variables
    leave_record = await get_leave_balance(
        db=db, 
        current_user=current_user,
        target_employee_id=payload.target_employee_id
    )
    
    # Returns the raw SQLAlchemy model object. 
    # FastAPI automatically handles serialization into LeaveBalanceResponse JSON.
    return leave_record