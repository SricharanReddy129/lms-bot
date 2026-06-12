import httpx
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Internal context storage for network-decoupled auth
from app.core.context import auth_token_var

# Global configuration for the API Gateway
API_BASE_URL = "http://localhost:8000/api/v1"

# =========================================================
# APPLICANT TOOL: View Personal Approved Leaves
# =========================================================

@tool
async def view_my_approved_leaves() -> Dict[str, Any]:
    """
    Retrieve the history of approved leave requests for the currently logged-in employee.
    Use this tool ONLY when an employee asks to see their own approved leaves or past time off.
    Takes no parameters.
    """
    # Retrieve JWT invisibly from the background request context
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/leaves/history/approved", 
            headers=headers
        )
        
        # Catch errors and return them cleanly
        if response.status_code == 404:
            return {"error": "No approved leave history found for your account."}
        elif response.status_code != 200:
            return {"error": f"Failed to fetch approved leaves. Status: {response.status_code}"}
            
        return response.json()
    

# =========================================================
# APPROVER ONLY TOOL: View Team Approved Leaves
# =========================================================

class TeamApprovedLeavesInput(BaseModel):
    employee_id: Optional[int] = Field(
        default=None, 
        description="The specific employee ID to check. Leave completely empty to fetch the approved history for the entire team."
    )

@tool(args_schema=TeamApprovedLeavesInput)
async def view_team_approved_leaves(
    employee_id: Optional[int]
) -> Dict[str, Any]:
    """
    Retrieve the history of approved leave requests for the team. 
    Can fetch history for everyone, or filter by a specific employee ID.
    This tool is strictly for managers and approvers checking past records.
    """
    # Retrieve JWT securely from the async request context
    # Keeps Pydantic schema completely clean of auth requirements
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Only attach the query parameter if the LLM extracted a specific ID
    params = {}
    if employee_id is not None:
        params["employee_id"] = employee_id
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/leaves/history/approved", 
            params=params, 
            headers=headers
        )
        
        # Intercept your backend's specific HTTP exceptions
        if response.status_code == 403:
            return {"error": "Permission Denied: You do not have permission to view other employees' approved leave history."}
        elif response.status_code == 404:
             return {"error": "No approved leaves found."}
        elif response.status_code != 200:
             return {"error": f"System error. Status: {response.status_code}"}
             
        return response.json()