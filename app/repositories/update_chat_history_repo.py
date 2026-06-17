from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import ChatHistory

async def update_chat_history(db: AsyncSession, employee_id: int, messages_json: list) -> None:
    """
    Updates the employee's chat history row with the newly pruned 15-message JSON array.
    """
    stmt = (
        update(ChatHistory)
        .where(ChatHistory.employee_id == employee_id)
        .values(messages=messages_json)
    )
    
    await db.execute(stmt)
    await db.commit()