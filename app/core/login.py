from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.login_repo import get_login_data
from app.repositories.name_repo import get_name_by_employee_id
from app.repositories.role_repo import get_role_by_employee_id
from app.api.interfaces import LoginInput, LoginResponse
from app.core import create_token

async def login(
        db : AsyncSession,
        payload: LoginInput
)-> LoginResponse:
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
    
    role = await get_role_by_employee_id(db, login_data.employee_id)
    employee_name = await get_name_by_employee_id(db, login_data.employee_id)

    token = create_token(
        employee_id=login_data.employee_id,
        employee_name=employee_name,
        role=role
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "employee_id": login_data.employee_id,
        "name": employee_name,
        "role": role
    }