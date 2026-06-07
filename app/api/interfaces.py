from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import date

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