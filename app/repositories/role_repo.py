from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import EmployeeRole

async def get_role_by_employee_id(
        db: AsyncSession,
        employee_id: int):
    stmt = select(EmployeeRole).where(EmployeeRole.employee_id == employee_id)
    result = await db.execute(stmt)

    return result.scalar_one_or_none()