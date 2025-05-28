# api/crud/feedback.py
import logging
import json
from typing import List, Dict, Any, Optional

from psycopg2.extras import Json as PsycopgJson
from .db_utils import db_session
from ..schemas.admin import parse_feedback_comment_for_admin

logger = logging.getLogger(__name__)

def get_all_feedback_from_db() -> List[Dict[str, Any]]:
    """Fetches and processes feedback data from the database conversations."""
    feedback_list = []
    try:
        with db_session() as cur:
            # Query conversations joining with users table to get username
            # Ensure messages and feedback_details are correctly accessed from JSONB
            cur.execute("""
                SELECT
                    c.id AS "ID Conversation",
                    c.timestamp AS "Date Conversation",
                    c.messages,
                    u.id AS "ID Utilisateur",
                    u.username AS "Utilisateur"
                FROM conversations c
                JOIN users u ON c.user_id = u.id
                WHERE jsonb_path_exists(c.messages, '$[*] ? (@.role == "assistant" && exists(@.feedback_details.rating))') -- Only get convos with feedback rating
                ORDER BY c.timestamp DESC
            """)
            conversations = cur.fetchall()

            for conv in conversations:
                messages = conv['messages']
                if not isinstance(messages, list): continue

                for i, msg in enumerate(messages):
                    if isinstance(msg, dict) and msg.get('role') == 'assistant':
                        feedback_details_raw = msg.get('feedback_details')
                        if isinstance(feedback_details_raw, dict) and feedback_details_raw.get('rating') is not None:
                            feedback_rating = feedback_details_raw.get('rating')
                            raw_comment_from_db = feedback_details_raw.get('comment')

                            parsed_category, parsed_details = None, None
                            if feedback_rating == 'down' and raw_comment_from_db:
                                parsed_category, parsed_details = parse_feedback_comment_for_admin(raw_comment_from_db)

                            # Find the user question that corresponds to this assistant message
                            # First try to get the message directly before
                            question_utilisateur = None
                            if i > 0 and isinstance(messages[i-1], dict) and messages[i-1].get('role') == 'user':
                                question_utilisateur = messages[i-1].get('content', '[Question manquante]')
                            else:
                                # If not found, search for the nearest preceding user message
                                for j in range(i-1, -1, -1):
                                    if isinstance(messages[j], dict) and messages[j].get('role') == 'user':
                                        question_utilisateur = messages[j].get('content', '[Question manquante]')
                                        break
                            
                            # If still not found, use a placeholder
                            if question_utilisateur is None:
                                question_utilisateur = '[Question non trouvée]'

                            feedback_entry = {
                                "Utilisateur": conv['Utilisateur'],
                                "ID Conversation": conv['ID Conversation'],
                                "Date Conversation": conv['Date Conversation'],
                                "Index Message": i,
                                "Message Assistant": msg.get('content', '[Contenu manquant]'),
                                "Question Utilisateur": question_utilisateur,
                                "Feedback Note": feedback_rating,
                                "Catégorie Problème": parsed_category,
                                "Détails Feedback": parsed_details,
                                "ID Utilisateur": conv['ID Utilisateur']
                            }
                            feedback_list.append(feedback_entry)

        return feedback_list
    except Exception as e:
        logger.error(f"Error fetching feedback from DB: {e}", exc_info=True)
        return [] # Return empty list on error


def clear_feedback_in_db(conversation_id: str, message_index: int, user_id_admin_check: int) -> bool:
    """
    Clears feedback details for a specific assistant message in a conversation.
    Includes an admin check on the user_id purely for logging/safety, authorization happens at router level.
    """
    logger.info(f"Admin {user_id_admin_check} attempting to clear feedback for conv {conversation_id}, msg index {message_index}")
    try:
        with db_session() as cur:
            # 1. Fetch current messages
            cur.execute("SELECT messages FROM conversations WHERE id = %s", (conversation_id,))
            result = cur.fetchone()
            if not result or not result['messages']:
                logger.warning(f"Feedback clear failed: Conversation {conversation_id} not found.")
                return False

            messages = result['messages']
            if not isinstance(messages, list):
                 logger.error(f"Feedback clear failed: Invalid messages format for conv {conversation_id}.")
                 return False

            # 2. Validate index and role
            if not (0 <= message_index < len(messages)) or messages[message_index].get('role') != 'assistant':
                logger.warning(f"Feedback clear failed: Invalid message index ({message_index}) or not an assistant message for conv {conversation_id}.")
                return False

            # 3. Check if feedback exists and clear it
            if 'feedback_details' in messages[message_index] and messages[message_index]['feedback_details'].get('rating') is not None:
                 messages[message_index]['feedback_details'] = {
                    'rating': None,
                    'problem_category': None,
                    'details': None
                 }
                 logger.info(f"Feedback details cleared for conv {conversation_id}, msg index {message_index}.")
            elif 'feedback_details' in messages[message_index]:
                 logger.info(f"Feedback already cleared for conv {conversation_id}, msg index {message_index}.")
                 return True # Already in desired state
            else:
                 logger.info(f"No feedback details found to clear for conv {conversation_id}, msg index {message_index}.")
                 return True # Already in desired state

            # 4. Update the database
            cur.execute(
                "UPDATE conversations SET messages = %s WHERE id = %s",
                (PsycopgJson(messages), conversation_id)
            )
            logger.info(f"Database updated for conv {conversation_id} after clearing feedback.")
            return True
    except Exception as e:
        logger.error(f"Error clearing feedback for conv {conversation_id}, msg index {message_index}: {e}", exc_info=True)
        # Rollback happens automatically in db_session context manager on exception
        return False