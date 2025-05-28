# api/schemas/token.py
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    requires_second_factor: bool = False
    user_id: int = None  # Only provided when requires_second_factor is True

class TokenData(BaseModel):
    username: str
    user_id: int
    is_admin: bool = False # Include admin status in token payload

