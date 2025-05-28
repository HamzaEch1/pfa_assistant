# api/dependencies/__init__.py
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import ollama

# Relative imports
from ..core.config import settings
from ..core import models as core_models
from ..crud import user as crud_user
from ..schemas.user import UserInDB

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_embedding_model_dependency() -> SentenceTransformer:
    """Dependency function to get the embedding model."""
    model = core_models.get_embedding_model()
    if model is None:
        logger.critical("Embedding model dependency not available.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Embedding model is not available")
    return model

def get_qdrant_client_dependency() -> QdrantClient:
    """Dependency function to get the Qdrant client."""
    client = core_models.get_qdrant_client()
    if client is None:
        logger.critical("Qdrant client dependency not available.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Vector database client is not available")
    return client

async def get_ollama_client_dependency() -> ollama.AsyncClient:
    """Dependency function to get the Ollama async client."""
    client = await core_models.get_ollama_client()
    if client is None:
        logger.critical("Ollama async client dependency not available.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM async client is not available")
    return client

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Dependency function to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            logger.warning(f"Token validation failed: username or id missing in payload.")
            raise credentials_exception
        # Fetch user details (you might want to cache this or check token validity differently)
        db_user = crud_user.get_user_by_username(username)
        if db_user is None or db_user.id != user_id:
             logger.warning(f"Token validation failed: User '{username}' not found or ID mismatch.")
             raise credentials_exception
        if not db_user.is_active:
            logger.warning(f"Token validation failed: User '{username}' is inactive.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        return db_user
    except JWTError as e:
        logger.warning(f"JWT decoding error: {e}", exc_info=False) # Avoid logging full trace for common JWT errors
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error during user authentication: {e}", exc_info=True)
        raise credentials_exception # Re-raise as 401 for safety