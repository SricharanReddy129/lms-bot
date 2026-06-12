import httpx
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Internal context storage for network-decoupled auth
from app.core.context import auth_token_var 

# Global configuration for the API Gateway
API_BASE_URL = "http://localhost:8000/api/v1"

# =========================================================
# APPROVER ONLY TOOL: Approve Pending Leaves
# =========================================================

class ApproveLeaveInput(BaseModel):
    leave_ids: List[int] = Field(
        ..., 
        min_length=1,
        description="A list of strictly numerical leave IDs to approve. Example: [42, 45]"
    )

@tool(args_schema=ApproveLeaveInput)
async def approve_leave_requests(
    leave_ids: List[int]
) -> Dict[str, Any]:
    """
    Approve one or multiple pending leave requests by their specific leave IDs.
    This tool is strictly reserved for managers and approvers.
    Use this tool whenever an approver explicitly instructs you to approve a leave.
    """
    # Retrieve JWT securely from the async request context (populated at the FastAPI route level)
    # This prevents the LLM from seeing or hallucinating auth parameters in the schema
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Construct the JSON payload matching the ApproveLeaveRequest Pydantic model
    payload = {
        "leave_ids": leave_ids
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/leaves/approve", 
            json=payload, 
            headers=headers
        )
        
        # Intercept backend security and validation errors to prevent Python crashes
        if response.status_code == 403:
            return {"error": "Permission Denied: You do not have manager privileges to approve leaves."}
        elif response.status_code == 404:
            return {"error": "Action Failed: No pending leaves found for the provided IDs. They may have already been processed or cancelled."}
        elif response.status_code == 422:
             return {"error": "Validation Error: The provided leave IDs were in an invalid format."}
        elif response.status_code != 200:
             return {"error": f"System error. Status: {response.status_code}"}
             
        # Returns the success dictionary with the hydrated receipts
        return response.json()