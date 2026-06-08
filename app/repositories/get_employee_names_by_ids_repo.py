from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import EmployeeData

async def get_employee_names_by_ids(db: AsyncSession, employee_ids: list):
    stmt = select(EmployeeData).where(EmployeeData.employee_id.in_(employee_ids))
    result = await db.execute(stmt)
    employees = result.scalars().all()
    return employees