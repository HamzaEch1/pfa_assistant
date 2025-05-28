# api/routers/auth.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm

# --- MODIFICATION START ---
# Import specific schemas directly
from ..schemas.token import Token
from ..schemas.user import User, UserCreateRequest, TwoFactorVerifyRequest, TwoFactorLoginRequest, TwoFactorSetupResponse
# --- MODIFICATION END ---

from .. import crud, core # Use relative imports
from ..core.security import create_access_token, get_current_user, TokenData # Import TokenData for get_current_user type hint
from ..core.two_factor import setup_2fa

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth", # Add a prefix for this router
    tags=["Authentication"] # Tag for OpenAPI docs
)

# --- MODIFICATION START ---
# Use the directly imported Token schema
@router.post("/login", response_model=Token)
# --- MODIFICATION END ---
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Logs in a user using username and password (OAuth2 password flow).
    Returns an access token or requires 2FA.
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    user = crud.user.authenticate_user(username=form_data.username, password=form_data.password)

    if not user:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if 2FA is enabled and confirmed for this user
    if user.two_factor_enabled and user.two_factor_confirmed:
        logger.info(f"2FA required for user: {form_data.username}")
        # Return a special response indicating 2FA is required
        return {
            "access_token": "",  # No access token yet
            "token_type": "bearer",
            "requires_second_factor": True,
            "user_id": user.id  # Include user ID for the 2FA verification step
        }

    # No 2FA required or 2FA not confirmed, proceed with normal login
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "is_admin": user.is_admin,
        "full_name": user.full_name
    }
    access_token = create_access_token(data=token_data)
    logger.info(f"Login successful, token generated for user: {form_data.username}")

    return {"access_token": access_token, "token_type": "bearer", "requires_second_factor": False}

@router.post("/verify-2fa", response_model=Token)
async def verify_2fa_login(verify_data: TwoFactorLoginRequest):
    """
    Verifies a 2FA code during login and returns an access token if valid.
    """
    logger.info(f"Verifying 2FA code for login, user ID: {verify_data.username}")
    
    # First authenticate the user to get their ID
    user = crud.user.get_user_by_username(verify_data.username)
    if not user:
        logger.warning(f"2FA verification failed: User '{verify_data.username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Verify the 2FA code
    if not crud.user.verify_2fa_code(user.id, verify_data.code):
        logger.warning(f"2FA verification failed: Invalid code for user '{verify_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification code",
        )
    
    # Code is valid, generate access token
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "is_admin": user.is_admin,
        "full_name": user.full_name
    }
    access_token = create_access_token(data=token_data)
    logger.info(f"2FA verification successful, token generated for user: {verify_data.username}")
    
    return {"access_token": access_token, "token_type": "bearer", "requires_second_factor": False}

@router.post("/signup", response_model=User)
async def create_user(user_data: UserCreateRequest):
    """
    Creates a new user account.
    """
    logger.info(f"Signup attempt for username: {user_data.username}")
    user = crud.user.create_user(user_data)
    if not user:
        logger.warning(f"Signup failed for username: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )
    logger.info(f"Signup successful for username: {user_data.username}")
    return user

# --- MODIFICATION START ---
# Use the directly imported User schema and TokenData from security
@router.get("/me", response_model=User)
async def read_users_me(current_user_token: TokenData = Depends(get_current_user)):
# --- MODIFICATION END ---
    """
    Returns the details of the currently authenticated user.
    """
    logger.debug(f"Fetching details for current user: {current_user_token.username} (ID: {current_user_token.user_id})")

    # Fetch user data from the database
    user = crud.user.get_user_by_id(current_user_token.user_id)
    if not user:
        logger.warning(f"User data not found for user ID: {current_user_token.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert to User model (which doesn't include password_hash)
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_admin=user.is_admin,
        is_active=user.is_active,
        two_factor_enabled=user.two_factor_enabled,
        two_factor_confirmed=user.two_factor_confirmed
    )

@router.post("/setup-2fa", response_model=TwoFactorSetupResponse)
async def setup_two_factor(current_user: TokenData = Depends(get_current_user)):
    """
    Sets up 2FA for the current user. Returns the secret and QR code.
    """
    logger.info(f"Setting up 2FA for user: {current_user.username}")
    
    # Get the setup information (secret and QR code)
    setup_info = setup_2fa(current_user.username)
    
    # Store the secret in the database 
    success = crud.user.enable_2fa_for_user(current_user.user_id, setup_info.secret)
    if not success:
        logger.error(f"Failed to enable 2FA for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable 2FA"
        )
    
    logger.info(f"2FA setup initialized for user: {current_user.username}")
    return setup_info

@router.post("/confirm-2fa")
async def confirm_two_factor(
    verify_data: TwoFactorVerifyRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Confirms 2FA setup by verifying the first code. Returns success status.
    """
    logger.info(f"Confirming 2FA for user: {current_user.username}")
    
    # Verify the code
    if not crud.user.verify_2fa_code(current_user.user_id, verify_data.code):
        logger.warning(f"2FA confirmation failed: Invalid code for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Mark 2FA as confirmed
    success = crud.user.confirm_2fa_for_user(current_user.user_id)
    if not success:
        logger.error(f"Failed to confirm 2FA for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm 2FA"
        )
    
    logger.info(f"2FA confirmed for user: {current_user.username}")
    return {"status": "success", "message": "2FA confirmed successfully"}

@router.post("/disable-2fa")
async def disable_two_factor(current_user: TokenData = Depends(get_current_user)):
    """
    Disables 2FA for the current user. Returns success status.
    """
    logger.info(f"Disabling 2FA for user: {current_user.username}")
    
    success = crud.user.disable_2fa_for_user(current_user.user_id)
    if not success:
        logger.error(f"Failed to disable 2FA for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )
    
    logger.info(f"2FA disabled for user: {current_user.username}")
    return {"status": "success", "message": "2FA disabled successfully"}