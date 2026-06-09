from typing import Annotated, Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolArg
import httpx

API_BASE_URL = "http://localhost:8000" 

# =========================================================
# 5. APPLICANT TOOL: View Personal Pending Leaves
# =========================================================

@tool
async def view_my_pending_leaves(
    auth_token: Annotated[str, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """
    Retrieve the pending leave requests for the currently logged-in employee.
    Use this tool ONLY when an employee asks to see their own pending leaves.
    Takes no parameters.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    
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
    target_employee_id: Optional[int],
    auth_token: Annotated[str, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """
    Retrieve pending leave requests for the team. 
    Can fetch requests for everyone, or filter by a specific employee ID.
    This tool is strictly for managers and approvers.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    
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
             return [{"error": f"No pending leaves found."}]
        elif response.status_code != 200:
             return [{"error": f"System error. Status: {response.status_code}"}]
             
        return response.json()