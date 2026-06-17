from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import ChatHistory
from sqlalchemy.dialects.mysql import insert as mysql_insert

async def upsert_chat_history(db: AsyncSession, employee_id: int, thread_id: str, messages_json: list) -> None:
    """
    Inserts a new row if the employee has no history, or updates the existing row.
    """
    # 1. Define the base insert statement
    stmt = mysql_insert(ChatHistory).values(
        employee_id=employee_id,
        thread_id=thread_id,
        messages=messages_json
        # updated_at is deliberately omitted so the DB engine handles it natively
    )
    
    # 2. Append the ON DUPLICATE KEY UPDATE clause
    # If the employee_id already exists, it will only overwrite the messages array
    upsert_stmt = stmt.on_duplicate_key_update(
        messages=stmt.inserted.messages,
        thread_id=stmt.inserted.thread_id
    )
    
    await db.execute(upsert_stmt)
    await db.commit()