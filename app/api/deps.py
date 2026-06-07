import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# This tells FastAPI to look for the token in the "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Intercepts the HTTP request, extracts the keyless JWT, 
    and decodes the payload without signature validation.
    """
    try:
        # Decode the token blindly. verify_signature=False is used because 
        # the token was created with algorithm="none"
        payload = jwt.decode(token, options={"verify_signature": False})
        
        employee_id: str = payload.get("id")
        role: str = payload.get("role")
        name: str = payload.get("name")
        
        if employee_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing context."
            )
            
        # Return the extracted context as a standard dictionary
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