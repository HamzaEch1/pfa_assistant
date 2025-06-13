# api/crud/user.py
import logging
from typing import Optional, List

from .db_utils import db_session
# --- CORRECTED IMPORTS ---
from ..schemas.user import User, UserCreate, UserInDB # Import base user schemas
from ..schemas.admin import UserAdminView # Import UserAdminView from admin schemas
# --- END CORRECTION ---
from ..core.security import get_password_hash, verify_password
from ..core.two_factor import setup_2fa, verify_totp

logger = logging.getLogger(__name__)

# --- Existing Functions (get_user_by_username, get_user_by_email, authenticate_user, create_user) ---
# Keep these as they are

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Retrieves a user by username."""
    # ... (keep existing implementation from your uploaded file) ...
    logger.debug(f"Attempting to retrieve user by username: {username}")
    try:
        with db_session() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_record = cur.fetchone()
            if user_record:
                logger.debug(f"User found: {username}")
                return UserInDB(**user_record) # Validate with Pydantic
            logger.debug(f"User not found: {username}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving user '{username}': {e}", exc_info=True)
        return None

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Retrieves a user by email."""
    # ... (keep existing implementation from your uploaded file) ...
    logger.debug(f"Attempting to retrieve user by email: {email}")
    if not email: return None
    try:
        with db_session() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user_record = cur.fetchone()
            if user_record:
                logger.debug(f"User found with email: {email}")
                return UserInDB(**user_record)
            logger.debug(f"User not found with email: {email}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving user by email '{email}': {e}", exc_info=True)
        return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticates a user. Returns the user object if valid, None otherwise."""
    # ... (keep existing implementation from your uploaded file) ...
    logger.info(f"Attempting authentication for user: {username}")
    user = get_user_by_username(username)
    if not user:
        logger.warning(f"Authentication failed: User '{username}' not found.")
        return None
    if not user.is_active:
        logger.warning(f"Authentication failed: User '{username}' is inactive.")
        return None
    if not verify_password(password, user.password_hash):
        logger.warning(f"Authentication failed: Incorrect password for user '{username}'.")
        return None
    logger.info(f"Authentication successful for user: {username}")
    return user

def create_user(user_in: UserCreate) -> Optional[UserAdminView]: # Changed return type hint
    """Creates a new user in the database."""
    # ... (keep existing implementation from your uploaded file, ensure RETURNING includes created_at) ...
    logger.info(f"Attempting to create user: {user_in.username}")

    if get_user_by_username(user_in.username):
        logger.warning(f"User creation failed: Username '{user_in.username}' already exists.")
        return None
    if user_in.email and get_user_by_email(user_in.email):
        logger.warning(f"User creation failed: Email '{user_in.email}' already exists.")
        return None

    password_hash = get_password_hash(user_in.password)
    try:
        with db_session() as cur:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, full_name, email, phone, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, username, full_name, email, phone, is_admin, is_active, created_at
                """, # Make sure created_at is returned
                (
                    user_in.username,
                    password_hash,
                    user_in.full_name,
                    user_in.email,
                    user_in.phone,
                    True # Activate user by default
                )
            )
            new_user_record = cur.fetchone()
            if new_user_record:
                logger.info(f"User '{user_in.username}' created successfully with ID {new_user_record['id']}.")
                return UserAdminView(**new_user_record) # Return extended view
            else:
                 logger.error(f"User creation failed for '{user_in.username}' despite no apparent error during insert.")
                 return None
    except Exception as e:
        logger.error(f"Error creating user '{user_in.username}': {e}", exc_info=True)
        return None

# --- NEW Admin Functions ---

def get_users(skip: int = 0, limit: int = 100) -> List[UserAdminView]:
    """Retrieves a list of users for admin view."""
    # ... (keep existing implementation from your uploaded file) ...
    logger.info(f"Fetching users list (skip={skip}, limit={limit})")
    users = []
    try:
        with db_session() as cur:
            cur.execute(
                "SELECT id, username, full_name, email, phone, is_admin, is_active, created_at FROM users ORDER BY username LIMIT %s OFFSET %s",
                (limit, skip)
            )
            records = cur.fetchall()
            for record in records:
                users.append(UserAdminView(**record))
        return users
    except Exception as e:
        logger.error(f"Error fetching user list: {e}", exc_info=True)
        return []


def delete_user_by_username(username: str) -> bool:
    """Deletes a user by username. Returns True if successful, False otherwise."""
    # ... (keep existing implementation from your uploaded file) ...
    if username == 'admin': # Or check against current logged-in admin from context if passed
        logger.warning(f"Attempt blocked to delete primary admin user '{username}'.")
        return False
    logger.info(f"Attempting to delete user: {username}")
    try:
        with db_session() as cur:
            cur.execute("DELETE FROM users WHERE username = %s", (username,))
            deleted_count = cur.rowcount
            if deleted_count > 0:
                 logger.info(f"Successfully deleted user '{username}'.")
                 return True
            else:
                 logger.warning(f"Delete failed: User '{username}' not found.")
                 return False
    except Exception as e:
        logger.error(f"Error deleting user '{username}': {e}", exc_info=True)
        return False

def update_user_admin_status(username: str, is_admin: bool) -> Optional[UserAdminView]:
    """Updates the admin status of a user."""
    # ... (keep existing implementation from your uploaded file) ...
    logger.info(f"Attempting to set admin status={is_admin} for user: {username}")
    try:
        with db_session() as cur:
            cur.execute(
                "UPDATE users SET is_admin = %s WHERE username = %s RETURNING id, username, full_name, email, phone, is_admin, is_active, created_at",
                (is_admin, username)
            )
            updated_user_record = cur.fetchone()
            if updated_user_record:
                logger.info(f"Admin status updated for user '{username}'.")
                return UserAdminView(**updated_user_record)
            else:
                logger.warning(f"Failed to update admin status: User '{username}' not found.")
                return None
    except Exception as e:
        logger.error(f"Error updating admin status for user '{username}': {e}", exc_info=True)
        return None

def update_user_email(user_id: int, new_email: str) -> Optional[UserAdminView]:
    """Updates the email for a specific user ID."""
    # ... (keep existing implementation from your uploaded file) ...
    logger.info(f"Attempting to update email for user ID {user_id} to {new_email}")
    existing_user = get_user_by_email(new_email)
    if existing_user and existing_user.id != user_id:
        logger.warning(f"Email update failed: '{new_email}' is already used by user ID {existing_user.id}.")
        return None

    try:
        with db_session() as cur:
            cur.execute(
                "UPDATE users SET email = %s WHERE id = %s RETURNING id, username, full_name, email, phone, is_admin, is_active, created_at",
                (new_email, user_id)
            )
            updated_user_record = cur.fetchone()
            if updated_user_record:
                logger.info(f"Email updated for user ID {user_id}.")
                return UserAdminView(**updated_user_record)
            else:
                logger.warning(f"Failed to update email: User ID {user_id} not found.")
                return None
    except Exception as e:
        logger.error(f"Error updating email for user ID {user_id}: {e}", exc_info=True)
        return None

def get_user_by_id(user_id: int) -> Optional[UserInDB]:
    """Retrieves a user by ID."""
    # ... (keep existing implementation from your previous correct version) ...
    logger.debug(f"Attempting to retrieve user by ID: {user_id}")
    try:
        with db_session() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user_record = cur.fetchone()
            if user_record:
                logger.debug(f"User found: ID {user_id}")
                return UserInDB(**user_record)
            logger.debug(f"User not found: ID {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving user ID '{user_id}': {e}", exc_info=True)
        return None

# --- 2FA Functions ---

def enable_2fa_for_user(user_id: int, two_factor_secret: str) -> bool:
    """Stores the 2FA secret for a user. Returns success status."""
    logger.info(f"Enabling 2FA for user ID: {user_id}")
    try:
        with db_session() as cur:
            cur.execute(
                """
                UPDATE users 
                SET two_factor_secret = %s, two_factor_enabled = TRUE
                WHERE id = %s
                """,
                (two_factor_secret, user_id)
            )
            if cur.rowcount > 0:
                logger.info(f"2FA enabled for user ID: {user_id}")
                return True
            else:
                logger.warning(f"Failed to enable 2FA: User ID {user_id} not found")
                return False
    except Exception as e:
        logger.error(f"Error enabling 2FA for user ID {user_id}: {e}", exc_info=True)
        return False

def confirm_2fa_for_user(user_id: int) -> bool:
    """Marks the user as having confirmed their 2FA setup."""
    logger.info(f"Confirming 2FA for user ID: {user_id}")
    try:
        with db_session() as cur:
            cur.execute(
                """
                UPDATE users 
                SET two_factor_confirmed = TRUE
                WHERE id = %s
                """,
                (user_id,)
            )
            if cur.rowcount > 0:
                logger.info(f"2FA confirmed for user ID: {user_id}")
                return True
            else:
                logger.warning(f"Failed to confirm 2FA: User ID {user_id} not found")
                return False
    except Exception as e:
        logger.error(f"Error confirming 2FA for user ID {user_id}: {e}", exc_info=True)
        return False

def disable_2fa_for_user(user_id: int) -> bool:
    """Disables 2FA for a user. Returns success status."""
    logger.info(f"Disabling 2FA for user ID: {user_id}")
    try:
        with db_session() as cur:
            cur.execute(
                """
                UPDATE users 
                SET two_factor_secret = NULL, two_factor_enabled = FALSE, two_factor_confirmed = FALSE
                WHERE id = %s
                """,
                (user_id,)
            )
            if cur.rowcount > 0:
                logger.info(f"2FA disabled for user ID: {user_id}")
                return True
            else:
                logger.warning(f"Failed to disable 2FA: User ID {user_id} not found")
                return False
    except Exception as e:
        logger.error(f"Error disabling 2FA for user ID {user_id}: {e}", exc_info=True)
        return False

def verify_2fa_code(user_id: int, code: str) -> bool:
    """Verifies a 2FA code for a user. Returns success status."""
    logger.info(f"Verifying 2FA code for user ID: {user_id}")
    try:
        # Get the user to access their 2FA secret
        user = get_user_by_id(user_id)
        if not user or not user.two_factor_secret or not user.two_factor_enabled:
            logger.warning(f"2FA verification failed: User {user_id} not found or 2FA not enabled")
            return False
            
        # Verify the code against the secret
        is_valid = verify_totp(user.two_factor_secret, code)
        if is_valid:
            logger.info(f"2FA verification successful for user ID: {user_id}")
        else:
            logger.warning(f"2FA verification failed: Invalid code for user ID {user_id}")
        
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying 2FA code for user ID {user_id}: {e}", exc_info=True)
        return False

def update_user_active_status(username: str, is_active: bool) -> Optional[UserAdminView]:
    """Updates the active status of a user."""
    logger.info(f"Updating active status for user '{username}' to {is_active}")
    try:
        with db_session() as cur:
            cur.execute(
                "UPDATE users SET is_active = %s WHERE username = %s RETURNING id, username, full_name, email, phone, is_admin, is_active, created_at",
                (is_active, username)
            )
            record = cur.fetchone()
            if record:
                return UserAdminView(**record)
            return None
    except Exception as e:
        logger.error(f"Error updating user active status: {e}", exc_info=True)
        return None