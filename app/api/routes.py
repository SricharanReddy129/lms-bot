from fastapi import APIRouter, Depends, Header, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

# Import your compiled graph and context variables
from app.agent.nodes import agent_app, init_context
from app.core.context import auth_token_var, db_session_var
from app.core.database import get_db

# Import the token extractor/setter dependency
from app.api.deps import get_and_set_auth_token

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
async def chat_endpoint(
    user_message: str = Body(..., embed=True), 
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Set the global context variables for Zero-Trust extraction
    token = authorization.split(" ")[1] if " " in authorization else authorization
    auth_token_var.set(token)
    db_session_var.set(db)
    
    # 2. Initialize state. (Remember: Node 1 handles historical_messages)
    initial_state = {
        "messages": [user_message]
    }
    
    # 3. The Filtered Generator
    async def token_generator():
        # Listen to all events happening inside the graph execution
        async for event in agent_app.astream_events(initial_state, version="v2"):
            kind = event["event"]
            
            # Filter strictly for the LLM generating a new token
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                
                # --- THE FILTERING LOGIC ---
                
                # Condition A: The LLM is writing JSON to call a tool. 
                # Ignore these chunks so they do not bleed into the UI.
                if chunk.tool_call_chunks:
                    continue
                
                # Condition B: The LLM is speaking to the user.
                # Yield the text immediately to the active HTTP connection.
                if chunk.content:
                    yield chunk.content

    # 4. Return the generator wrapped in a FastAPI StreamingResponse
    return StreamingResponse(token_generator(), media_type="text/event-stream")