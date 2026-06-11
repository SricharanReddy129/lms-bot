from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from langchain_core.messages import HumanMessage
from app.agent.graph import agent_app # Your compiled LangGraph application

from app.core.database import get_db
from app.api.deps import get_current_user
from app.api.interfaces import ApprovedHistoryRequest, LeaveBalanceResponse, LeaveBalanceRequest, HolidayCalendarResponse
from app.api.interfaces import LeaveApplicationRequest, LeaveApplicationResponse, PendingLeavesRequest, PendingLeavesResponse
from app.api.interfaces import ApproveLeaveRequest, ApproveLeaveResponse, RejectLeaveRequest, RejectLeaveResponse
from app.api.interfaces import ApprovedHistoryResponse, RejectedHistoryResponse, RejectedHistoryFilter
from app.api.interfaces import ChatRequest
from app.services.approve_leaves_service import approve_leaves as approve_leaves_service
from app.services.approved_leaves_service import get_approved_leaves_service
from app.services.get_rejected_leaves_service import get_rejected_leaves_service
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

security = HTTPBearer()

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

@router.get("/leaves/history/approved", response_model=ApprovedHistoryResponse)
async def get_approved_history(
    filters: ApprovedHistoryRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await get_approved_leaves_service(
        db=db,
        current_user=current_user,
        target_employee_id=filters.employee_id
    )

@router.get("/leaves/history/rejected", response_model=RejectedHistoryResponse)
async def get_rejected_history(
    filters: RejectedHistoryFilter = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return await get_rejected_leaves_service(
        db=db,
        current_user=current_user,
        target_employee_id=filters.employee_id
    )

@router.post("/chat")
async def chat_with_agent(
    payload: ChatRequest,
    # FastAPI automatically pulls the token from the browser's Authorization header
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    raw_token = credentials.credentials
    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication token missing")

    # Pack the user's message and the token into the initial graph state
    initial_state = {
        "messages": [HumanMessage(content=payload.message)],
        "auth_token": raw_token
    }

    try:
        # Run the LangGraph execution loop asynchronously
        final_state = await agent_app.ainvoke(initial_state)
        
        # Grab the very last message generated by the LLM
        ai_response = final_state["messages"][-1].content
        
        return {
            "status": "success",
            "response": ai_response
        }
        
    except Exception as e:
        # Catch configuration or runtime errors gracefully
        raise HTTPException(
            status_code=500, 
            detail=f"Agent execution failed: {str(e)}"
        )