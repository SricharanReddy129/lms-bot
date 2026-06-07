from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# ---------------------------------------
# INPUT SCHEMAS (Ingress Validation)
# ---------------------------------------

class LeaveBalanceInput(BaseModel):
    target_employee_id: Optional[int] = None

class LoginInput(BaseModel):
    employee_email : EmailStr
    password : str

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