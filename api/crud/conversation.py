# api/crud/conversation.py
import logging
import datetime
import json
from typing import List, Dict, Optional
from psycopg2.extras import Json as PsycopgJson # Use Json adapter for inserting JSONB
# from fastapi import HTTPException, status

from .db_utils import db_session
# --- MODIFICATION START ---
# Import specific schemas directly from their module
# Assuming Conversation schema is in message.py as originally generated
from ..schemas.message import Conversation, FeedbackData
# --- MODIFICATION END ---

logger = logging.getLogger(__name__)

# NOTE: These functions are synchronous. Consider asyncpg for production.

# --- MODIFICATION START ---
# Use the directly imported Conversation schema
def get_conversation_by_id(conv_id: str, user_id: int) -> Optional[Conversation]:
# --- MODIFICATION END ---
    """Retrieves a specific conversation for a user."""
    logger.debug(f"Attempting to retrieve conversation {conv_id} for user {user_id}")
    try:
        with db_session() as cur:
            cur.execute(
                "SELECT * FROM conversations WHERE id = %s AND user_id = %s",
                (conv_id, user_id)
            )
            record = cur.fetchone()
            if record:
                messages_data = record['messages']
                if isinstance(messages_data, str):
                    try:
                        messages_data = json.loads(messages_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not decode messages JSON for conv_id {record['id']}")
                        messages_data = []

                conversation_data = {**record, "messages": messages_data}
                # Use imported Conversation directly
                return Conversation(**conversation_data)
            logger.debug(f"Conversation {conv_id} not found for user {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving conversation {conv_id} for user {user_id}: {e}", exc_info=True)
        return None

# --- MODIFICATION START ---
# Use the directly imported Conversation schema
def get_user_conversations(user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
# --- MODIFICATION END ---
    """Loads conversations for a specific user with pagination."""
    logger.debug(f"Loading conversations for user {user_id} (limit: {limit}, skip: {skip})")
    conversations = []
    try:
        with db_session() as cur:
            cur.execute(
                "SELECT * FROM conversations WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s OFFSET %s",
                (user_id, limit, skip)
            )
            records = cur.fetchall()
            for record in records:
                messages_data = record['messages']
                if isinstance(messages_data, str):
                    try: messages_data = json.loads(messages_data)
                    except: messages_data = []
                conversation_data = {**record, "messages": messages_data}
                try:
                     # Use imported Conversation directly
                     conversations.append(Conversation(**conversation_data))
                except Exception as pydantic_error:
                     logger.warning(f"Skipping conversation {record.get('id')} due to Pydantic validation error: {pydantic_error}")

            logger.info(f"Loaded {len(conversations)} conversations for user {user_id}")
            return conversations
    except Exception as e:
        logger.error(f"Error loading conversations for user {user_id}: {e}", exc_info=True)
        return []


# --- MODIFICATION START ---
# Use the directly imported Conversation schema
def save_conversation(conversation_data: Conversation) -> bool:
# --- MODIFICATION END ---
    """Saves or updates a conversation for a specific user."""
    logger.info(f"Saving conversation {conversation_data.id} for user {conversation_data.user_id}")
    try:
        with db_session() as cur:
            # Supprimer le log des messages avant la sauvegarde
            # messages_to_save_raw = conversation_data.messages
            # messages_to_save_for_json = [msg.model_dump() for msg in messages_to_save_raw]
            # logger.debug(f"Messages being prepared for DB save (Python dicts): {json.dumps(messages_to_save_for_json, indent=2, default=str)}")

            cur.execute(
                """
                INSERT INTO conversations (id, user_id, title, timestamp, messages)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    timestamp = EXCLUDED.timestamp,
                    messages = EXCLUDED.messages
                WHERE conversations.user_id = %s;
                """,
                (
                    conversation_data.id,
                    conversation_data.user_id,
                    conversation_data.title,
                    conversation_data.timestamp,
                    # Rétablir la version originale pour PsycopgJson
                    PsycopgJson(conversation_data.model_dump()['messages'] if hasattr(conversation_data, 'model_dump') else conversation_data.dict()['messages']),
                    conversation_data.user_id
                )
            )
        logger.info(f"Conversation {conversation_data.id} saved successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving conversation {conversation_data.id}: {e}", exc_info=True)
        return False


def delete_conversation(conv_id: str, user_id: int) -> bool:
    """Deletes a conversation ensuring it belongs to the user."""
    logger.info(f"Attempting to delete conversation {conv_id} for user {user_id}")
    try:
        with db_session() as cur:
            cur.execute(
                "DELETE FROM conversations WHERE id = %s AND user_id = %s",
                (conv_id, user_id)
            )
            deleted_count = cur.rowcount
            if deleted_count > 0:
                 logger.info(f"Successfully deleted conversation {conv_id} for user {user_id}.")
                 return True
            else:
                 logger.warning(f"Delete operation: Conversation {conv_id} not found or user {user_id} mismatch.")
                 return False
    except Exception as e:
        logger.error(f"Error deleting conversation {conv_id} for user {user_id}: {e}", exc_info=True)
        return False

# --- NEW FUNCTION FOR FEEDBACK ---
def save_feedback_for_message(conv_id: str, user_id: int, message_index: int, feedback_data: FeedbackData) -> bool:
    """Saves user feedback to a specific assistant message within a conversation."""
    logger.info(f"Attempting to save feedback (Rating: {feedback_data.rating}) for message {message_index} in conversation {conv_id} by user {user_id}")
    
    conversation = get_conversation_by_id(conv_id=conv_id, user_id=user_id)
    if not conversation:
        logger.warning(f"Cannot save feedback: Conversation {conv_id} not found for user {user_id}")
        return False
    
    if not isinstance(conversation.messages, list) or message_index < 0 or message_index >= len(conversation.messages):
        logger.warning(f"Cannot save feedback: Invalid message_index {message_index} for conversation {conv_id} (length: {len(conversation.messages) if isinstance(conversation.messages, list) else 'N/A'})")
        return False
        
    # Get the message object (assuming it's mutable, like a dict or Pydantic model)
    message_to_update = conversation.messages[message_index]

    # Ensure it's an assistant message
    # The schema might have role directly, or it might be a dict key
    message_role = getattr(message_to_update, 'role', None) or message_to_update.get('role', None)
    if message_role != 'assistant':
        logger.warning(f"Cannot save feedback: Message at index {message_index} in conv {conv_id} is not an assistant message (role: {message_role}).")
        return False

    # Add or update the feedback details
    feedback_details_dict = feedback_data.model_dump() # Pydantic v2 or dict() for v1
    
    # How to add it depends on whether message_to_update is a dict or object
    if isinstance(message_to_update, dict):
        message_to_update['feedback_details'] = feedback_details_dict
    elif hasattr(message_to_update, 'feedback_details'): # If Message schema has feedback_details field
        # This requires Message schema to be updated to include: 
        # feedback_details: Optional[FeedbackData] = None
        message_to_update.feedback_details = feedback_data # Assign the Pydantic model directly if schema allows
    else:
        # Fallback: If it's an object without the field, try adding it dynamically (might not work depending on object)
        # Or better: Update the Message schema definition first.
        # For now, log a warning if schema is not prepared.
        logger.warning(f"Message object at index {message_index} (type: {type(message_to_update)}) does not seem prepared for feedback_details. Update Message schema.")
        # Attempt dynamic assignment (less safe)
        try:
             setattr(message_to_update, 'feedback_details', feedback_details_dict)
             logger.info("Dynamically added 'feedback_details' to message object.")
        except AttributeError:
              logger.error("Could not dynamically add 'feedback_details' to message object.")
              return False # Cannot save feedback

    logger.debug(f"Updated message at index {message_index} with feedback: {feedback_details_dict}")

    # Save the entire conversation with the modified message
    success = save_conversation(conversation_data=conversation)
    if success:
        logger.info(f"Feedback saved successfully for message {message_index} in conversation {conv_id}.")
    else:
        logger.error(f"Failed to save conversation {conv_id} after updating feedback for message {message_index}.")
        
    return success
# --- END NEW FUNCTION ---