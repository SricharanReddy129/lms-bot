from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import LeaveBalance

async def get_leave_balance_by_employee_id(
                                            db: AsyncSession, 
                                            employee_id: int
                                        ):
    stmt = select(LeaveBalance).where(LeaveBalance.employee_id == employee_id)
    result = await db.execute(stmt)
    
    return result.scalar_one_or_none()

