from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import HolidaysCalendar

async def get_all_holidays(db: AsyncSession):
    stmt = select(HolidaysCalendar).order_by(HolidaysCalendar.holiday_date)
    result = await db.execute(stmt)
    
    return result.scalars().all()