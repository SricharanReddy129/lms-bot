from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Literal, List
from datetime import date

# --- SHARED RECEIPT RECORD ---
class ProcessedLeaveRecord(BaseModel):
    leave_id: int
    employee_id: int
    employee_name: str
    leave_type: str

class RejectLeaveItem(BaseModel):
    leave_id: int
    reason: str

class HistoryApprovedRecord(BaseModel):
    history_id: int        # The 'sno' from the approved_leaves table
    original_leave_id: int # The 'leave_id' tracking the original request
    employee_id: int
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date

class HistoryRejectedRecord(BaseModel):
    history_id: int
    original_leave_id: int
    employee_id: int
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    applicant_reason: Optional[str]
    approver_reason: str

# ---------------------------------------
# INPUT SCHEMAS (Ingress Validation)
# ---------------------------------------

class LeaveBalanceRequest(BaseModel):
    target_employee_id: Optional[int] = None

class LoginRequest(BaseModel):
    employee_email : EmailStr
    password : str

class LeaveApplicationRequest(BaseModel):
    start_date: date
    end_date: date
    leave_type: Literal["earned", "sick", "parental"]
    reason: Optional[str] = Field(None, max_length=1000)

class PendingLeavesRequest(BaseModel):
    target_employee_id: Optional[int] = None

class ApproveLeaveRequest(BaseModel):
    leave_ids: List[int] = Field(..., min_items=1)

class RejectLeaveRequest(BaseModel):
    rejections: List[RejectLeaveItem] = Field(..., min_items=1)

class ApprovedHistoryRequest(BaseModel):
    employee_id: Optional[int] = None

class RejectedHistoryFilter(BaseModel):
    employee_id: Optional[int] = None

class ChatRequest(BaseModel):
    message: str

# ---------------------------------------
# OUTPUT SCHEMAS (Egress Serialization)
# ---------------------------------------

class LeaveBalanceResponse(BaseModel):
    employee_id: int
    earned_leaves: int
    sick_leaves: int
    parental_leaves: int

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee_id: int
    name: str
    role: str

class HolidayCalendarResponse(BaseModel):
    sno: int
    holiday_name: str
    holiday_date: date

    # This tells Pydantic to read data like `holiday.holiday_name` 
    # instead of expecting a dictionary like `holiday["holiday_name"]`
    model_config = ConfigDict(from_attributes=True)

class LeaveApplicationResponse(BaseModel):
    status: str

class PendingLeavesResponse(BaseModel):
    leave_id: int
    employee_id: int
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None

class ApproveLeaveResponse(BaseModel):
    status: str = "success"
    message: str = "Leaves successfully approved."
    data: List[ProcessedLeaveRecord]

class RejectLeaveResponse(BaseModel):
    status: str = "success"
    message: str = "Leaves successfully rejected."
    data: List[ProcessedLeaveRecord]

class ApprovedHistoryResponse(BaseModel):
    status: str = "success"
    message: str = "Approved leave history retrieved successfully."
    data: List[HistoryApprovedRecord]

class RejectedHistoryResponse(BaseModel):
    status: str = "success"
    message: str = "Rejected leave history retrieved successfully."
    data: List[HistoryRejectedRecord]