# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

app = FastAPI(title="LMS Bot API")

@app.get("/health/db")
async def test_database_connection(db: AsyncSession = Depends(get_db)):
    try:
        # Execute a simple ping to the Aiven database
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        
        return {
            "status": "success", 
            "message": "Database connected perfectly to Aiven!",
            "ping_result": value
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": "Connection failed", 
            "details": str(e)
        }