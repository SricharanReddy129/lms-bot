import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# Internal context storage for network-decoupled auth
from app.core.context import auth_token_var

API_BASE_URL = "http://localhost:8000/api/v1" 

# =========================================================
# 5. APPLICANT TOOL: View Personal Pending Leaves
# =========================================================

@tool
async def view_my_pending_leaves() -> List[Dict[str, Any]]:
    """
    Retrieve the pending leave requests or can be called as applied leaves
    for the currently logged-in employee.
    Use this tool ONLY when an employee asks to see their own pending leaves.
    Takes no parameters.
    """
    # Retrieve JWT invisibly from the background request context
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/leaves/pending", headers=headers)
        
        # Catch errors and return them cleanly inside a list format
        if response.status_code == 404:
            return [{"error": "No pending leaves found."}]
        elif response.status_code != 200:
            return [{"error": f"Failed to fetch pending leaves. Status: {response.status_code}"}]
            
        return response.json()


# =========================================================
# 6. APPROVER ONLY TOOL: View Team Pending Leaves
# =========================================================

class TeamPendingLeavesInput(BaseModel):
    target_employee_id: Optional[int] = Field(
        default=None, 
        description="The specific employee ID to check. Leave completely empty to fetch all pending requests for the entire team."
    )

@tool(args_schema=TeamPendingLeavesInput)
async def view_team_pending_leaves(
    target_employee_id: Optional[int]
) -> List[Dict[str, Any]]:
    """
    Retrieve pending leave requests or can be called as applied leaves for the team. 
    Can fetch requests for everyone, or filter by a specific employee ID.
    This tool is strictly for managers and approvers.
    """
    # Retrieve JWT securely from the async request context
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Only attach the query parameter if the LLM extracted a specific ID
    params = {}
    if target_employee_id is not None:
        params["target_employee_id"] = target_employee_id
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/leaves/pending", 
            params=params, 
            headers=headers
        )
        
        # Intercept your backend's specific HTTP exceptions
        if response.status_code == 403:
            return [{"error": "Permission Denied: You do not have permission to view other employees' pending leaves."}]
        elif response.status_code == 404:
             return [{"error": "No pending leaves found."}]
        elif response.status_code != 200:
             return [{"error": f"System error. Status: {response.status_code}"}]
             
        return response.json()