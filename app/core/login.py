from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.login_repo import get_login_data
from app.repositories.name_repo import get_name_by_employee_id
from app.repositories.role_repo import get_role_by_employee_id
from app.api.interfaces import LoginRequest, LoginResponse
from app.core.create_token import create_token

async def login(
        db: AsyncSession,
        payload: LoginRequest
) -> LoginResponse:
    
    # 1. Authenticate User
    login_data = await get_login_data(db, payload.employee_email)

    if not login_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found for email {payload.employee_email}."
        )
    
    if login_data.password != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password."
        )
    
    # 2. Fetch the raw SQLAlchemy Row Objects from the database
    role_record = await get_role_by_employee_id(db, login_data.employee_id)
    name_record = await get_name_by_employee_id(db, login_data.employee_id)

    # 3. EXTRACT THE PURE STRINGS (This fixes the JSON serializable error)
    # We use dot-notation matching your exact database column names
    actual_role_string = role_record.employee_role
    actual_name_string = name_record.employee_name

    # 4. Generate the token using the pure strings
    token = create_token(
        employee_id=login_data.employee_id,
        employee_name=actual_name_string,
        role=actual_role_string
    )

    # 5. Return the dictionary using the pure strings
    return {
        "access_token": token,
        "token_type": "bearer",
        "employee_id": login_data.employee_id,
        "name": actual_name_string,
        "role": actual_role_string
    }