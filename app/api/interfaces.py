from pydantic import BaseModel, Field
from typing import Optional

class Config:
    # Pydantic V2 config to allow this schema to extract data directly from an SQLAlchemy model instance
    from_attributes = True

# ---------------------------------------
# INPUT SCHEMAS (Ingress Validation)
# ---------------------------------------

class LeaveBalanceQueryInput(BaseModel):
    """
    Validates the incoming query parameters.
    Used by the agent/client when trying to view a leave balance.
    """
    employee_id: int


# ---------------------------------------
# OUTPUT SCHEMAS (Egress Serialization)
# ---------------------------------------

class LeaveBalanceResponse(BaseModel):
    """
    Sanitizes the raw SQLAlchemy database row before sending JSON back to the agent.
    Notice 'sno' (the DB primary key) is deliberately excluded to protect internal architecture.
    """
    employee_id: int
    earned_leaves: int
    sick_leaves: int
    parental_leaves: int
