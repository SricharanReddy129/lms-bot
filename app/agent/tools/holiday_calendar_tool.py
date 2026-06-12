import httpx
from typing import Dict, Any, List
from langchain_core.tools import tool

# Internal context storage for network-decoupled auth
from app.core.context import auth_token_var 

# In a real setup, this comes from your app.core.config
API_BASE_URL = "http://localhost:8000/api/v1" 

@tool
async def view_holiday_calendar() -> List[Dict[str, Any]]:
    """
    Retrieve the official company holiday calendar.
    Use this tool whenever the user asks about upcoming holidays, company days off, or public holidays.
    Takes zero parameters.
    """
    # Retrieve JWT invisibly from the background request context
    token = auth_token_var.get()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/holidays", headers=headers)
        
        if response.status_code != 200:
            # We return a list containing an error dict so it matches the expected return signature
            return [{"error": f"Failed to fetch holidays. Status: {response.status_code}"}]
            
        return response.json()