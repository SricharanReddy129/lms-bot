import httpx
from typing import Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Internal context storage for network-decoupled auth
from app.core.context import auth_token_var 

# Global configuration for the API Gateway
API_BASE_URL = "http://localhost:8000"

# =========================================================
# APPLICANT TOOL: View Personal Leave Balance
# =========================================================

@tool
async def view_my_leave_balance() -> Dict[str, Any]:
    """
    Retrieve the personal leave balance entitlements (casual, sick, earned leaves) 
    for the currently logged-in employee.
    Use this tool whenever the user asks about their own leave balance.
    Takes zero parameters.
    """
    # Retrieve JWT invisibly from the background request context
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/leaves/balance", headers=headers)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch balance. Status: {response.status_code}", "details": response.text}
            
        return response.json()
    


class EmployeeLeaveBalanceInput(BaseModel):
    target_employee_id: int = Field(
        ..., 
        description="The strict numerical employee ID of the team member whose leave balance needs to be checked."
    )

@tool(args_schema=EmployeeLeaveBalanceInput)
async def view_employee_leave_balance(
    target_employee_id: int
) -> Dict[str, Any]:
    """
    Retrieve the leave balance entitlements for a specific team member by their employee ID.
    This tool is strictly reserved for managers and approvers checking on subordinates.
    """
    # Retrieve JWT securely from the async request context
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {"target_employee_id": target_employee_id}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/leaves/balance", params=params, headers=headers)
        
        # Intercept backend security and validation errors cleanly
        if response.status_code == 403:
            return {"error": "Permission Denied: You do not have manager access to view this employee's records."}
        elif response.status_code == 404:
            return {"error": f"Employee ID {target_employee_id} not found."}
        elif response.status_code != 200:
             return {"error": f"System error. Status: {response.status_code}"}
             
        return response.json()