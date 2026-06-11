import httpx
from datetime import date
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool


from app.core.context import auth_token_var 

# Global configuration for the API Gateway
API_BASE_URL = "http://localhost:8000"

class LeaveApplicationInput(BaseModel):
    start_date: date = Field(
        ..., 
        description="The start date of the leave in YYYY-MM-DD format."
    )
    end_date: date = Field(
        ..., 
        description="The end date of the leave in YYYY-MM-DD format (inclusive)."
    )
    leave_type: Literal["earned", "sick", "parental"] = Field(
        ..., 
        description="The category of leave being requested. Must strictly be one of: 'earned', 'sick', or 'parental'."
    )
    reason: Optional[str] = Field(
        default=None, 
        max_length=1000, 
        description="An optional brief explanation or justification for the leave request."
    )

# CHANGE 3: The tool decorator remains untouched, perfectly binding to the clean Pydantic schema.
@tool(args_schema=LeaveApplicationInput)
async def apply_for_leave(
    start_date: date,
    end_date: date,
    leave_type: Literal["earned", "sick", "parental"],
    reason: Optional[str]
) -> Dict[str, Any]:
    """
    Submit a new leave application request on behalf of the logged-in employee.
    Use this tool whenever an employee explicitly requests to book, take, or apply for time off.
    """
    # Fetch the token invisibly from the request's background memory context.
    token = auth_token_var.get()
    
    # Construct the header using the extracted context token.
    headers = {"Authorization": f"Bearer {token}"}
    
    # Construct the JSON payload, forcing dates to strings for HTTP transmission
    payload = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "leave_type": leave_type,
        "reason": reason
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/leaves/apply", 
            json=payload, 
            headers=headers
        )
        
        # Capture the 400 Bad Request if they do not have enough leave balance
        if response.status_code == 400:
            error_data = response.json()
            return {"error": "Leave application failed", "details": error_data.get("detail", "Bad Request")}
        elif response.status_code != 200:
            return {"error": f"System error. Status: {response.status_code}"}
            
        return response.json()