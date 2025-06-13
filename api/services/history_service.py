# api/services/history_service.py
import logging
import uuid
import datetime
from typing import List, Optional

import ollama
from ..core.config import settings

# --- MODIFICATION START ---
# Import specific schemas directly from their module
from ..schemas.message import Message, Conversation
# --- MODIFICATION END ---

from .. import crud

logger = logging.getLogger(__name__)

# The _extract_topic_from_question function and its associated [TITLE_DEBUG] prints are removed.

# --- MODIFICATION START ---
# Use the directly imported Message schema
def generate_conversation_title(messages: List[Message]) -> str:
# --- MODIFICATION END ---
    """Generates a concise, non-question title reflecting the topic of the conversation using an LLM."""
    logger.info("[LLM_TITLE_GEN] Attempting to generate title with LLM.")

    if not messages or len(messages) < 1:
        logger.warning("[LLM_TITLE_GEN] Not enough messages to generate title.")
        return "Nouvelle conversation"

    # Extract first user message content
    first_user_message_obj = next((msg for msg in messages if msg.role == "user" and msg.content), None)
    if not first_user_message_obj:
        logger.warning("[LLM_TITLE_GEN] No user message found for title base.")
        return "Nouvelle conversation"
    
    first_user_message_content = first_user_message_obj.content.replace("\n", " ").strip()
    if not first_user_message_content:
        logger.warning("[LLM_TITLE_GEN] User message content for title base is empty.")
        return "Nouvelle conversation"

    llm_generated_title = None
    try:
        client = ollama.Client(host=settings.OLLAMA_HOST)
        
        llm_prompt = ""
        user_question = first_user_message_content # Use already extracted and cleaned version
        assistant_answer = ""

        # Try to get first assistant answer if available
        if len(messages) >= 2:
            assistant_answer_obj = next((msg for msg in messages if msg.role == "assistant" and msg.content), None)
            if assistant_answer_obj:
                assistant_answer = assistant_answer_obj.content.replace("\n", " ").strip()

        if user_question and assistant_answer:
            prompt_user_q = (user_question[:200] + '...') if len(user_question) > 200 else user_question
            prompt_assistant_a = (assistant_answer[:200] + '...') if len(assistant_answer) > 200 else assistant_answer
            llm_prompt = (
                f'Question de l\'utilisateur: "{prompt_user_q}"\n'
                f'Première réponse de l\'assistant: "{prompt_assistant_a}"\n\n'
                f'Basé sur cette interaction, crée un titre de conversation court et pertinent (environ 3-74mots). '
                f'Ce titre ne doit PAS être une question. Le titre doit être en français.\n'
                f'Titre suggéré:'
            )
        elif user_question: # Fallback if only user question is effectively available
            prompt_user_q = (user_question[:250] + '...') if len(user_question) > 250 else user_question
            llm_prompt = (
                f'Reformule la question suivante pour en faire un titre de conversation concis et pertinent '
                f'(environ 5-7 mots, pas une question) : "{prompt_user_q}". '
                f'Le titre doit être en français.\nTitre : '
            )
        else: # Should not be reached if first_user_message_content was validated
            logger.error("[LLM_TITLE_GEN] User question content became empty unexpectedly before prompt generation.")
            return "Nouvelle conversation"

        logger.info(f"[LLM_TITLE_GEN] Prompting LLM with: {llm_prompt}")
        response = client.chat(
            model=settings.OLLAMA_MODEL_NAME,
            messages=[{'role': 'user', 'content': llm_prompt}],
            options={'temperature': 0.3}
        )
        
        raw_title = response['message']['content'].strip()
        logger.info(f"[LLM_TITLE_GEN] LLM raw response: '{raw_title}'")
        
        cleaned_title = ""
        lines = raw_title.splitlines() # Split into lines
        for line in lines:
            potential_title = line.strip().replace('"', '').replace("'", "") # Clean the line
            if potential_title: # If the cleaned line is not empty
                cleaned_title = potential_title
                break # Stop after finding the first non-empty line

        # Remove prefixes like "Titre:" just in case they are on the first line
        prefixes_to_remove = ["titre suggéré:", "titre:"]
        for prefix in prefixes_to_remove:
            if cleaned_title.lower().startswith(prefix):
                cleaned_title = cleaned_title[len(prefix):].strip()
                break 
        
        if cleaned_title and len(cleaned_title) > 3: # Basic validity check
            llm_generated_title = cleaned_title
            logger.info(f"[LLM_TITLE_GEN] LLM cleaned title (first line): '{llm_generated_title}'")
        else:
            logger.warning(f"[LLM_TITLE_GEN] LLM generated title was empty or too short after cleaning first line: '{cleaned_title}'")

    except Exception as e:
        logger.error(f"[LLM_TITLE_GEN] Error during LLM title generation: {e}", exc_info=True)

    title_candidate = ""
    if llm_generated_title:
        title_candidate = llm_generated_title
    else:
        logger.warning("[LLM_TITLE_GEN] LLM title generation failed or result was unsuitable. Using fallback.")
        fallback_text = first_user_message_content # Already cleaned
        if fallback_text.endswith("?") or fallback_text.endswith("؟"):
            fallback_text = fallback_text[:-1].strip()
        
        if fallback_text and len(fallback_text) > 1:
            title_candidate = "Sujet : " + fallback_text
        else:
            logger.info("[LLM_TITLE_GEN] Fallback text also too short. Defaulting to 'Nouvelle conversation'.")
            return "Nouvelle conversation"

    if title_candidate and title_candidate[0].islower(): # Capitalize first letter
        title_candidate = title_candidate[0].upper() + title_candidate[1:]

    max_len = 50
    ellipsis = "..."
    final_title = title_candidate

    if len(title_candidate) > max_len:
        if title_candidate.startswith("Sujet : ") and max_len > len("Sujet : ") + len(ellipsis) + 2:
             content_part = title_candidate[len("Sujet : "):]
             available_len_for_content = max_len - len("Sujet : ") - len(ellipsis)
             final_title = "Sujet : " + content_part[:available_len_for_content] + ellipsis
        else:
            final_title = title_candidate[:max_len - len(ellipsis)] + ellipsis
    
    if len(final_title.replace(ellipsis, "").strip()) < 3:
        logger.warning(f"[LLM_TITLE_GEN] Final title ('{final_title}') too short. Defaulting to 'Nouvelle conversation'.")
        return "Nouvelle conversation"

    logger.info(f"[LLM_TITLE_GEN] Successfully generated title: '{final_title}'")
    return final_title

# --- MODIFICATION START ---
# Use the directly imported Conversation schema
def start_new_conversation(user_id: int) -> Optional[Conversation]:
# --- MODIFICATION END ---
    """Creates and saves a new empty conversation."""
    logger.info(f"Starting new conversation for user {user_id}")
    new_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware datetime

    # Use imported Conversation directly
    new_conversation = Conversation(
        id=new_id,
        user_id=user_id,
        title="Nouvelle conversation", # Initial title
        timestamp=now,
        messages=[] # Start with empty messages
    )

    if crud.conversation.save_conversation(new_conversation):
        logger.info(f"New conversation {new_id} created and saved for user {user_id}")
        return new_conversation
    else:
        logger.error(f"Failed to save new conversation {new_id} for user {user_id}")
        return None

# --- MODIFICATION START ---
# Use the directly imported Conversation and Message schemas
def add_message_and_save(
    conversation_id: str,
    user_id: int,
    user_message: Message,
    assistant_message: Message
) -> Optional[Conversation]:
# --- MODIFICATION END ---
    """Adds user and assistant messages to a conversation and saves it."""
    logger.info(f"Adding messages to conversation {conversation_id} for user {user_id}")
    conversation = crud.conversation.get_conversation_by_id(conversation_id, user_id)

    if not conversation:
        logger.error(f"Cannot add messages: Conversation {conversation_id} not found for user {user_id}")
        return None

    conversation.messages.append(user_message)
    conversation.messages.append(assistant_message)

    if len(conversation.messages) == 2: # user + assistant = 2
         logger.info(f"Conversation {conversation_id} has 2 messages. Attempting to generate title.") # LOG DE TEST AJOUTÉ
         conversation.title = generate_conversation_title(conversation.messages)

    conversation.timestamp = datetime.datetime.now(datetime.timezone.utc)

    if crud.conversation.save_conversation(conversation):
        logger.info(f"Messages added and conversation {conversation_id} updated.")
        return conversation
    else:
        logger.error(f"Failed to save updated conversation {conversation_id}")
        return None