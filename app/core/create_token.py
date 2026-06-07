import jwt
from datetime import datetime, timezone

def create_token(employee_id: int, employee_name: str, role: str) -> str:
    """
    Generates a keyless, unsigned, and permanently valid JSON Web Token (JWT).
    Designed for architectures where an upstream API Gateway handles signing and revocation.
    """
    payload = {
        "sub": str(employee_id),
        "iat": datetime.now(timezone.utc),       # Issued at timestamp
        
        # Custom Context Data (Used by your RBAC Services)
        "id": employee_id,
        "name": employee_name,
        "role": role
    }
    
    # Using algorithm="none" and an empty key creates a keyless token string.
    # Omitting the "exp" claim entirely makes the token valid forever.
    encoded_jwt = jwt.encode(payload, key="", algorithm="none")
    
    return encoded_jwt