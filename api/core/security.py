# api/core/security.py
import jwt
import hashlib
import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, Security, status, Depends
from fastapi.security import OAuth2PasswordBearer

from .config import settings
# --- MODIFICATION START ---
# Import specific schemas directly
from ..schemas.token import TokenData
# --- MODIFICATION END ---

# This scheme will look for the 'Authorization: Bearer <token>' header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login") # Adjust tokenUrl to your login endpoint path

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS)

    to_encode.update({"exp": expire, "iat": datetime.datetime.now(datetime.timezone.utc)})
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    except jwt.PyJWTError as e:
        print(f"Error encoding JWT: {e}") # Log the error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create access token")


# --- MODIFICATION START ---
# Use the directly imported TokenData schema
def verify_token(token: str = Depends(oauth2_scheme)) -> TokenData:
# --- MODIFICATION END ---
    """
    Verifies a JWT token provided via the OAuth2 scheme.
    Returns the token payload (TokenData schema) if valid.
    Raises HTTPException otherwise.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        user_id: Optional[int] = payload.get("user_id")
        is_admin: Optional[bool] = payload.get("is_admin")

        if username is None or user_id is None:
            print(f"Token verification failed: Missing 'sub' or 'user_id'. Payload: {payload}")
            raise credentials_exception

        token_data = TokenData(username=username, user_id=user_id, is_admin=is_admin or False) # Default is_admin to False if missing
        return token_data

    except jwt.ExpiredSignatureError:
        print("Token verification failed: Expired signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        print(f"Token verification failed: JWT Error - {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Token verification failed: Unexpected error - {e}")
        raise credentials_exception


def get_password_hash(password: str) -> str:
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    return get_password_hash(plain_password) == hashed_password

# Dependency to get the current user from the token
# --- MODIFICATION START ---
# Use the directly imported TokenData schema
async def get_current_user(token_data: TokenData = Depends(verify_token)) -> TokenData:
# --- MODIFICATION END ---
    return token_data

# --- MODIFICATION START ---
# Use the directly imported TokenData schema
async def get_current_active_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
# --- MODIFICATION END ---
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user