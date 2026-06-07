import jwt
from fastapi import Depends, HTTPException, status

# 1. Import HTTPBearer instead of OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 2. Initialize the standard bearer security scheme
security = HTTPBearer()

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