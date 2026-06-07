from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import EmployeePassword

async def get_login_data(
        db: AsyncSession,
        employee_email: str):
    stmt = select(EmployeePassword).where(EmployeePassword.employee_email_id == employee_email)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()