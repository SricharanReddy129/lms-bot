import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 2. Initialize the standard bearer security scheme
security = HTTPBearer()

# Import the locker
from app.core.context import auth_token_var, db_session_var

from app.core.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession

# 3. Change the dependency input to expect standard credentials
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Intercepts the HTTP request, extracts the Bearer token, 
    and decodes the payload without signature validation.
    """
    # 4. Extract the actual token string from the credentials object
    token = credentials.credentials
    
    try:
        # Decode the token blindly, allowing the "none" algorithm
        payload = jwt.decode(
            token, 
            options={"verify_signature": False}, 
            algorithms=["none"]
        )
        
        employee_id: str = payload.get("id")
        role: str = payload.get("role")
        name: str = payload.get("name")
        
        if employee_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing context."
            )
            
        return {
            "id": int(employee_id),
            "role": role,
            "name": name
        }
        
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode credentials."
        )
    
async def get_and_set_auth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extracts the JWT token from the incoming HTTP request header 
    and securely stores it in the background context variable for the duration of the request.
    """
    token = credentials.credentials
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    # THE CRITICAL STEP: Drop the token into the background context memory.
    # From this exact millisecond forward, any tool executed within this 
    # specific API request thread can call `auth_token_var.get()` to find it.
    auth_token_var.set(token)
    
    return token

async def get_and_set_db_session(
    db: AsyncSession = Depends(get_db)
) -> AsyncSession:
    """
    Extracts the database session from the FastAPI dependency and 
    securely stores it in the background context variable for the duration of the request.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database session could not be established.")
    
    # Store the DB session in the context variable for global access
    db_session_var.set(db)
    
    return db