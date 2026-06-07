from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the repository layer execution function
from app.repositories.get_all_holidays_repo import get_all_holidays as fetch_all_holidays

async def get_all_holidays(db: AsyncSession):
    # 1. Call the database repository
    holidays = await fetch_all_holidays(db)

    # 2. Translate empty results into API-friendly errors
    if not holidays:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No holidays found in the calendar."
        )

    return holidays