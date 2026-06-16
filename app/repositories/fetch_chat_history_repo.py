from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import ChatHistory

async def fetch_chat_history_from_mysql(db: AsyncSession, employee_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetches the raw JSON stored in the messages column for the given employee.
    """
    stmt = select(ChatHistory).where(ChatHistory.employee_id == employee_id)
    result = await db.execute(stmt)
    
    record = result.scalars().first()
    
    if record:
        # Directly returning the raw JSON dictionary from the database
        return record.messages
        
    return None