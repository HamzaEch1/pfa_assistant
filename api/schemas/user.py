# api/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Base properties shared by user models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

# Properties required during user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Properties received via API on creation (e.g., signup form)
class UserCreateRequest(UserCreate):
    pass # Currently same as UserCreate, but allows future divergence

# Properties stored in DB (excluding password)
class UserInDBBase(UserBase):
    id: int
    is_admin: bool = False
    is_active: bool = True
    two_factor_enabled: bool = False
    two_factor_confirmed: bool = False

    class Config:
        from_attributes = True # Pydantic V2 compatibility (formerly orm_mode)

# Properties to return to client (never include password hash)
class User(UserInDBBase):
    pass

# Properties stored in DB including the hashed password
class UserInDB(UserInDBBase):
    password_hash: str
    two_factor_secret: Optional[str] = None

# 2FA Setup Response
class TwoFactorSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code: str  # Base64 encoded QR code image

# 2FA Verification Request
class TwoFactorVerifyRequest(BaseModel):
    code: str

# 2FA Login Request
class TwoFactorLoginRequest(BaseModel):
    username: str
    code: str

