from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# ---------------------------------------------------------
# 1. FRONTEND PAGE ROUTES
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend"])
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get("/chat", response_class=HTMLResponse, tags=["Frontend"])
async def serve_chat(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")

# ---------------------------------------------------------
# 2. PUBLIC ROUTES (Open to the internet)
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