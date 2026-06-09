import httpx
from typing import Annotated, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolArg

# Global configuration for the API Gateway
API_BASE_URL = "http://localhost:8000"

# =========================================================
# APPROVER ONLY TOOL: Reject Pending Leaves
# =========================================================

class RejectLeaveItem(BaseModel):
    leave_id: int = Field(
        ..., 
        description="The specific numerical ID of the leave request to reject."
    )
    reason: str = Field(
        ..., 
        description="The mandatory justification or reason for rejecting this specific leave request."
    )

class RejectLeaveInput(BaseModel):
    rejections: List[RejectLeaveItem] = Field(
        ..., 
        min_length=1,
        description="A list of leave requests to reject, each containing the leave_id and a mandatory reason."
    )

@tool(args_schema=RejectLeaveInput)
async def reject_leave_requests(
    rejections: List[RejectLeaveItem],
    auth_token: Annotated[str, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Reject one or multiple pending leave requests by their specific leave IDs.
    A valid reason MUST be provided for every rejected leave.
    This tool is strictly reserved for managers and approvers.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Construct the JSON payload matching the backend's RejectLeaveRequest model
    payload = {
        "rejections": [
            {"leave_id": item.leave_id, "reason": item.reason} 
            for item in rejections
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{API_BASE_URL}/leaves/reject", 
            json=payload, 
            headers=headers
        )
        
        # Intercept backend security and validation errors gracefully
        if response.status_code == 403:
            return {"error": "Permission Denied: You do not have manager privileges to reject leaves."}
        elif response.status_code == 404:
            return {"error": "Action Failed: No pending leaves found for the provided IDs. They may have already been processed."}
        elif response.status_code == 422:
             return {"error": "Validation Error: Ensure a valid numerical ID and a text reason are provided for every rejection."}
        elif response.status_code != 200:
             return {"error": f"System error. Status: {response.status_code}"}
             
        # Returns the success dictionary with the hydrated receipts
        return response.json()