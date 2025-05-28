# api/crud/db_utils.py
import psycopg2
from psycopg2.extras import DictCursor
import logging
from contextlib import contextmanager
from typing import Generator, Any

from ..core.config import settings

logger = logging.getLogger(__name__)

# NOTE: This uses the synchronous psycopg2 driver from the original project.
# For optimal performance with FastAPI's async capabilities, consider migrating
# to an asynchronous driver like 'asyncpg' and using libraries like 'SQLAlchemy 2.0+'
# or 'databases'. This current implementation will work but might block the event loop
# under heavy load.

def get_db_connection():
    """Establishes a synchronous connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            dbname=settings.PG_DB,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD
        )
        logger.debug("Database connection established.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error ({settings.PG_HOST}): {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to DB: {e}", exc_info=True)
        return None

@contextmanager
def db_session() -> Generator[psycopg2.extensions.cursor, Any, None]:
    """Provides a database session (cursor) using a context manager."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn:
            # Use DictCursor to get results as dictionaries
            cur = conn.cursor(cursor_factory=DictCursor)
            logger.debug("Database session started.")
            yield cur
            conn.commit() # Commit changes if no exceptions occurred
            logger.debug("Database session committed.")
        else:
            raise ConnectionError("Failed to establish database connection")
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        if conn:
            conn.rollback() # Rollback changes on error
            logger.warning("Database session rolled back due to error.")
        raise # Re-raise the exception so API endpoints can handle it
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        logger.debug("Database connection closed.")


# --- Database Initialization (Adapted from original database.py) ---
# This should ideally be run once, perhaps via a startup script or CLI command,
# rather than checked on every API startup.
def init_db():
    """Initializes the database schema if tables don't exist."""
    logger.info("Attempting DB Initialization...")
    try:
        with db_session() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(100) NOT NULL,
                    full_name VARCHAR(100),
                    email VARCHAR(100) UNIQUE,
                    phone VARCHAR(20),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    two_factor_secret VARCHAR(50),
                    two_factor_confirmed BOOLEAN DEFAULT FALSE
                )
            """)
            logger.info("Checked/Created 'users' table.")

            # Alter users table to add 2FA columns if they don't exist
            try:
                # Check if two_factor_enabled column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='two_factor_enabled'
                """)
                
                if not cur.fetchone():
                    # Add the 2FA columns if they don't exist
                    cur.execute("""
                        ALTER TABLE users 
                        ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE,
                        ADD COLUMN two_factor_secret VARCHAR(50),
                        ADD COLUMN two_factor_confirmed BOOLEAN DEFAULT FALSE
                    """)
                    logger.info("Added 2FA columns to users table")
            except Exception as e:
                logger.error(f"Error checking/adding 2FA columns: {e}", exc_info=True)

            # Create conversations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(36) PRIMARY KEY, -- Assuming UUID stored as string
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL, -- Use TIMESTAMPTZ
                    messages JSONB NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            logger.info("Checked/Created 'conversations' table.")

            # Insert default admin user if not present
            cur.execute("SELECT 1 FROM users WHERE username = %s LIMIT 1", ('admin',))
            if not cur.fetchone():
                from ..core.security import get_password_hash # Local import
                default_admin_pass = 'admin123' # CHANGE THIS IN PRODUCTION
                password_hash = get_password_hash(default_admin_pass)
                cur.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, is_admin, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ('admin', password_hash, 'Administrateur', 'admin@example.com', True, True))
                logger.warning("Default admin user 'admin' created with password 'admin123'. CHANGE THIS PASSWORD!")

        logger.info("Database initialization check complete.")
        return True
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)
        return False

