# api/routers/admin.py
import logging
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks,
    Path,
    Query,
    Body
)
from qdrant_client import QdrantClient, models as qdrant_models
from sentence_transformers import SentenceTransformer

# Relative imports for schemas, crud, services, dependencies
from ..schemas.admin import (
    UserAdminView,
    FeedbackEntry,
    CatalogInfoResponse,
    CatalogUploadResponse,
    AdminConfigResponse,
    UpdateAdminEmailRequest
)
from ..schemas.user import User # For response on email update
from ..core.config import settings
from ..core.security import TokenData, get_current_active_admin # Security dependency
from ..crud import user as crud_user
from ..crud import feedback as crud_feedback
from ..services import admin_service # Import the background task logic
from ..dependencies import get_qdrant_client_dependency, get_embedding_model_dependency # Import dependencies

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_active_admin)] # Require admin for all routes in this router
)

# --- User Management Endpoints ---

@router.get("/users", response_model=List[UserAdminView])
async def read_users(skip: int = 0, limit: int = 100):
    """Retrieves a list of users (Admin only)."""
    logger.info(f"Admin action: Fetching users (skip={skip}, limit={limit})")
    users = crud_user.get_users(skip=skip, limit=limit)
    return users

@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: str = Path(..., description="The username of the user to delete"),
    current_admin: TokenData = Depends(get_current_active_admin) # Re-inject for self-deletion check
):
    """Deletes a user by username (Admin only)."""
    if username == current_admin.username:
        logger.warning(f"Admin {username} attempted self-deletion.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin users cannot delete their own account.")

    logger.info(f"Admin action: Deleting user '{username}'")
    success = crud_user.delete_user_by_username(username=username)
    if not success:
        # Distinguish between not found and other errors if needed from CRUD
        logger.warning(f"Admin action: Failed to delete user '{username}' (not found or other error).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or deletion failed")
    return None # Return None for 204 response

@router.put("/users/{username}/admin-status", response_model=UserAdminView)
async def set_user_admin_status(
    is_admin: bool = Body(..., embed=True), # Expect {"is_admin": true/false} in body
    username: str = Path(..., description="The username of the user to modify")
):
    """Sets the admin status for a user (Admin only)."""
    logger.info(f"Admin action: Setting admin status to {is_admin} for user '{username}'")
    updated_user = crud_user.update_user_admin_status(username=username, is_admin=is_admin)
    if not updated_user:
        logger.warning(f"Admin action: Failed to update admin status for user '{username}' (not found or other error).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or update failed")
    return updated_user

@router.put("/users/{user_id}/email", response_model=User)
async def update_user_email_route(
     request: UpdateAdminEmailRequest,
     user_id: int = Path(..., description="ID of the user whose email to update"),
     current_admin: TokenData = Depends(get_current_active_admin) # Ensure only admin can call
):
     """Updates the email of a specific user (Admin only)."""
     logger.info(f"Admin action: Updating email for user ID {user_id}.")
     if not request.new_email or '@' not in request.new_email:
         raise HTTPException(status_code=400, detail="Valid email required")

     updated_user = crud_user.update_user_email(user_id=user_id, new_email=request.new_email)
     if not updated_user:
          # Check if error was due to email already existing
          existing = crud_user.get_user_by_email(request.new_email)
          if existing:
               raise HTTPException(status_code=400, detail="Email already in use by another account.")
          else:
               raise HTTPException(status_code=404, detail="User not found or failed to update email.")
     # Return standard User schema, not UserAdminView, unless specifically needed
     return User(**updated_user.model_dump())


# --- Feedback Endpoints ---

@router.get("/feedback", response_model=List[FeedbackEntry])
async def read_feedback():
    """Retrieves all feedback entries from conversations (Admin only)."""
    logger.info("Admin action: Fetching all feedback.")
    feedback_data = crud_feedback.get_all_feedback_from_db()
    # Pydantic will automatically validate based on the response_model alias mapping
    return feedback_data

@router.delete("/feedback/{conversation_id}/{message_index}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_feedback(
    conversation_id: str = Path(..., description="ID of the conversation"),
    message_index: int = Path(..., ge=0, description="Index of the assistant message within the conversation"),
    current_admin: TokenData = Depends(get_current_active_admin) # Pass admin for logging
):
    """Clears feedback for a specific message (Admin only)."""
    logger.info(f"Admin action: Clearing feedback for conv {conversation_id}, msg index {message_index}")
    success = crud_feedback.clear_feedback_in_db(
        conversation_id=conversation_id,
        message_index=message_index,
        user_id_admin_check=current_admin.user_id # Pass admin ID for logging in CRUD
    )
    if not success:
        logger.warning(f"Admin action: Failed to clear feedback for conv {conversation_id}, msg index {message_index}.")
        # Return 404 if conversation/message not found, maybe 500 for other errors?
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found or could not be cleared")
    return None

# --- Catalog Endpoints ---

@router.post("/catalog/upload", response_model=CatalogUploadResponse)
async def upload_catalog_file(
    background_tasks: BackgroundTasks,
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dependency),
    embedding_model: SentenceTransformer = Depends(get_embedding_model_dependency),
    file: UploadFile = File(..., description="Excel file (.xlsx) containing catalog data")
):
    """
    Uploads an Excel file to update the Qdrant data catalog.
    Processing happens in the background (Admin only).
    """
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only .xlsx files are accepted.")

    logger.info(f"Admin action: Received catalog upload file: {file.filename}")

    try:
        # Read file content into memory - careful with very large files
        contents = await file.read()
        # Add the processing to background tasks
        background_tasks.add_task(
            admin_service.process_and_upsert_excel_task,
            file_content=contents,
            filename=file.filename,
            qdrant_client=qdrant_client, # Pass dependencies needed by the task
            embedding_model=embedding_model
        )
        logger.info(f"Added background task for processing file: {file.filename}")
        return CatalogUploadResponse(filename=file.filename)
    except Exception as e:
         logger.error(f"Error handling catalog upload for file {file.filename}: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate file processing: {e}")
    finally:
         await file.close()

# >>> CORRECTED FUNCTION <<<
@router.get("/catalog/info", response_model=CatalogInfoResponse)
async def get_catalog_info(
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dependency)
):
    """Gets information about the Qdrant data catalog collection (Admin only)."""
    logger.info("Admin action: Requesting catalog info.")
    collection_name = settings.QDRANT_COLLECTION_NAME
    try:
        # Get collection information
        collection_info = qdrant_client.get_collection(collection_name=collection_name)
        logger.debug(f"Raw collection info retrieved: {collection_info}") # Add debug log

        # --- CORRECTED ACCESS TO VECTOR DIMENSION ---
        dim = None
        # Check if the expected path exists
        if (hasattr(collection_info, 'config') and
            hasattr(collection_info.config, 'params') and
            hasattr(collection_info.config.params, 'vectors')):

            vectors_params = collection_info.config.params.vectors

            # Check if vectors_params is a single VectorParams object (unnamed vector)
            if isinstance(vectors_params, qdrant_models.VectorParams):
                dim = vectors_params.size
                logger.debug(f"Found unnamed vector params with size: {dim}")
            # Check if vectors_params is a dictionary (named vectors)
            elif isinstance(vectors_params, dict):
                # Try to get the default unnamed vector config ('') or the first named one
                vector_config = vectors_params.get('') or next(iter(vectors_params.values()), None)
                if vector_config and isinstance(vector_config, qdrant_models.VectorParams):
                    dim = vector_config.size
                    logger.debug(f"Found named vector params, using first/default size: {dim}")
                else:
                    logger.warning("Vector params structure is a dict, but couldn't extract valid VectorParams.")
            else:
                 logger.warning(f"Unexpected type for vectors_params: {type(vectors_params)}")
        else:
             logger.warning("Could not find vector configuration path in collection_info.")
        # --- END CORRECTION ---

        return CatalogInfoResponse(
            collection_name=collection_name,
            points_count=collection_info.points_count, # points_count should exist directly
            vectors_dimension=dim # Use the extracted dimension
        )
    except Exception as e:
        logger.error(f"Failed to get Qdrant collection info for '{collection_name}': {e}", exc_info=True)
        detail_message = f"Could not retrieve info for collection '{collection_name}'"
        # More robust check for "not found" based on potential exception types from qdrant-client
        if "not found" in str(e).lower() or (hasattr(e, 'status_code') and e.status_code == 404):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Collection '{collection_name}' not found.")
        else:
            # Keep raising 503 for other errors (like connection issues previously handled)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"{detail_message}: {e}")
# >>> END CORRECTED FUNCTION <<<


# --- Admin Config Endpoints ---

@router.get("/config", response_model=AdminConfigResponse)
async def get_admin_config(current_admin: TokenData = Depends(get_current_active_admin)):
     """Gets admin configuration details (Admin only)."""
     logger.info(f"Admin action: Fetching admin config for user {current_admin.username}")
     # Fetch the 'admin' user specifically, as the config seems tied to that user in admin_setup.py
     admin_user = crud_user.get_user_by_username('admin') # Fetch the user named 'admin'
     if not admin_user or not admin_user.is_admin:
         # This case implies the 'admin' user doesn't exist or isn't admin, which is a config problem
         logger.error("Configuration error: Default 'admin' user not found or is not admin.")
         raise HTTPException(status_code=500, detail="Admin configuration error")

     # Add logic to fetch authorized emails if implemented later
     return AdminConfigResponse(admin_email=admin_user.email)

@router.put("/config/admin-email", response_model=User)
async def update_admin_email_route(
     request: UpdateAdminEmailRequest,
     current_admin: TokenData = Depends(get_current_active_admin)
):
     """Updates the email of the primary 'admin' user account (Admin only)."""
     logger.info(f"Admin action: User {current_admin.username} updating primary admin email.")
     if not request.new_email or '@' not in request.new_email:
         raise HTTPException(status_code=400, detail="Valid email required")

     # Find the primary 'admin' user ID
     admin_user_record = crud_user.get_user_by_username('admin')
     if not admin_user_record:
          raise HTTPException(status_code=404, detail="Primary admin user 'admin' not found.")

     # Update the email for the 'admin' user ID
     updated_user = crud_user.update_user_email(user_id=admin_user_record.id, new_email=request.new_email)
     if not updated_user:
          # Check if error was due to email already existing
          existing = crud_user.get_user_by_email(request.new_email)
          if existing and existing.id != admin_user_record.id:
               raise HTTPException(status_code=400, detail="Email already in use by another account.")
          else:
               logger.error(f"Failed to update email for primary admin user ID {admin_user_record.id}")
               raise HTTPException(status_code=500, detail="Failed to update admin email.")

     return User(**updated_user.model_dump()) # Return standard User schema