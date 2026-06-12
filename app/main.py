from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.api.interfaces import LoginRequest, LoginResponse
from app.core.login import login

# Import the strictly private domain router
from app.api.routes import router as service_router
from app.api.routes import router as agent_router

load_dotenv()

app = FastAPI(title="LMS Bot API")

# ---------------------------------------------------------
# 1. PUBLIC ROUTES (Open to the internet)
# ---------------------------------------------------------

@app.post("/login", response_model=LoginResponse, tags=["Public"])
async def authenticate_user(
    payload: LoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to authenticate a user and generate a JWT.
    """
    result = await login(db, payload)
    return result


@app.get("/health/db", tags=["System"])
async def test_database_connection(db: AsyncSession = Depends(get_db)):
    """
    Public endpoint to verify Aiven database connectivity.
    """
    try:
        await db.execute(text("SELECT 1"))
        result = await db.execute(text("SHOW TABLES"))
        tables = result.scalars().all()
        
        return {
            "status": "success", 
            "message": "Database connected perfectly to Aiven!",
            "tables_found": tables
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": "Connection failed", 
            "details": str(e)
        }

# ---------------------------------------------------------
# 2. PRIVATE ROUTES (Locked down)
# ---------------------------------------------------------

# Mount the domain router. Because it was defined with 
# dependencies=[Depends(get_current_user)], it is completely secure.
app.include_router(service_router)