from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.api.interfaces import LeaveBalanceResponse, LeaveBalanceRequest, HolidayCalendarResponse
from app.api.interfaces import LeaveApplicationRequest, LeaveApplicationResponse, PendingLeavesRequest, PendingLeavesResponse
from app.api.interfaces import ApproveLeaveRequest, ApproveLeaveResponse, RejectLeaveRequest, RejectLeaveResponse
from app.services.approve_leaves_service import approve_leaves as approve_leaves_service
from app.services.leave_balance_service import get_leave_balance
from app.services.get_all_holidays_services import get_all_holidays
from app.services.apply_leave_service import apply_for_leave as apply_for_leave_service
from app.services.get_pending_leaves_service import get_pending_leaves as get_pending_leaves_service
from app.services.reject_leave_service import reject_leaves_service

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
    payload: LeaveBalanceRequest = Depends(),
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

@router.get("/holidays", response_model=List[HolidayCalendarResponse])
async def fetch_holidays(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Your service logic that returns a list of HolidayCalendar objects
    holidays = await get_all_holidays(db)
    return holidays

@router.post("/leaves/apply", response_model=LeaveApplicationResponse)
async def apply_for_leave(
    payload: LeaveApplicationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await apply_for_leave_service(db, current_user, payload)
    return result

@router.get("/leaves/pending", response_model=List[PendingLeavesResponse])
async def fetch_pending_leaves(
    payload: PendingLeavesRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Unpack the Pydantic input and current user dictionary into pure variables
    pending_leaves = await get_pending_leaves_service(
        db=db, 
        current_user=current_user,
        target_employee_id=payload.target_employee_id
    )
    
    # Returns the raw SQLAlchemy model object. 
    # FastAPI automatically handles serialization into PendingLeavesResponse JSON.
    return pending_leaves

@router.post("/leaves/approve", response_model=ApproveLeaveResponse)
async def approve_leaves(
    payload: ApproveLeaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Your service logic that approves the leaves and returns an ApproveLeaveResponse
    result = await approve_leaves_service(
        db,
        current_user,
        payload.leave_ids)
    return result

@router.put("/leaves/reject", response_model=RejectLeaveResponse)
async def reject_leaves(
    request: RejectLeaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 1. Strip the Pydantic objects into a native Python list of dictionaries
    # Result: [{"leave_id": 42, "reason": "Busy"}, ...]
    rejections_list = [item.model_dump() for item in request.rejections]

    # 2. Pass only primitive data down to the business logic
    return await reject_leaves_service(
        db=db,
        current_user=current_user,
        rejections_data=rejections_list
    )