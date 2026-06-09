import httpx
from typing import Annotated, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolArg

# In a real setup, this comes from your app.core.config
API_BASE_URL = "http://localhost:8000" 

# =========================================================
# 1. APPLICANT TOOL: View Personal Leave Balance
# =========================================================

@tool
async def view_my_leave_balance(
    auth_token: Annotated[str, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Retrieve the personal leave balance entitlements (casual, sick, earned leaves) 
    for the currently logged-in employee.
    Use this tool whenever the user asks about their own leave balance.
    Takes zero parameters.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/leaves/balance", headers=headers)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch balance. Status: {response.status_code}", "details": response.text}
            
        return response.json()


# =========================================================
# 2. APPROVER ONLY TOOL: View Team Member Leave Balance
# =========================================================

class EmployeeLeaveBalanceInput(BaseModel):
    target_employee_id: int = Field(
        ..., 
        description="The strict numerical employee ID of the team member whose leave balance needs to be checked."
    )

@tool(args_schema=EmployeeLeaveBalanceInput)
async def view_employee_leave_balance(
    target_employee_id: int,
    auth_token: Annotated[str, InjectedToolArg]
) -> Dict[str, Any]:
    """
    Retrieve the leave balance entitlements for a specific team member by their employee ID.
    This tool is strictly reserved for managers and approvers checking on subordinates.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    params = {"target_employee_id": target_employee_id}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/leaves/balance", params=params, headers=headers)
        
        # If the backend rejects the manager, pass the rejection cleanly to the LLM
        if response.status_code == 403:
            return {"error": "Permission Denied: You do not have manager access to view this employee's records."}
        elif response.status_code == 404:
            return {"error": f"Employee ID {target_employee_id} not found."}
        elif response.status_code != 200:
             return {"error": f"System error. Status: {response.status_code}"}
             
        return response.json()
