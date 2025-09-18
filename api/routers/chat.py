# api/routers/chat.py
import logging
import datetime
import uuid
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File, Form, Path, Request
from fastapi.responses import Response, FileResponse
from sentence_transformers import SentenceTransformer
import ollama
from ..core.config import settings
from ..core.security import get_current_user, TokenData # Import TokenData RESTORED

# Import necessary schemas from message.py
from ..schemas.message import Message, ChatRequest, ChatResponse, Conversation, ConversationCreate, FileMetadata, FileUploadResponse, FeedbackData
# --- IMPORT CRUD DIRECTLY ---
from .. import crud, services # Import crud and services
# --- END IMPORT ---
from ..dependencies import (
    get_embedding_model_dependency,
    get_qdrant_client_dependency,
    get_ollama_client_dependency
)
from qdrant_client import QdrantClient # Import types for dependency injection hints
from ..services.rag_service import ClientDisconnectedError # Importer l'exception personnalisÃ©e


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
    dependencies=[Depends(get_current_user)] # Applies auth to all routes
)

# Use the directly imported Conversation schema
@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Starts a new, empty conversation for the current user.
    """
    logger.info(f"User {current_user.user_id} requesting new conversation.")
    # Service layer handles creation logic (which calls CRUD)
    new_conversation = services.history_service.start_new_conversation(user_id=current_user.user_id)
    if not new_conversation:
        logger.error(f"Failed to create new conversation for user {current_user.user_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not start new conversation")
    return new_conversation

# File upload endpoint for conversations
@router.post("/conversations/{conversation_id}/upload", response_model=FileUploadResponse)
async def upload_file_to_conversation(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    embedding_model: SentenceTransformer = Depends(get_embedding_model_dependency),
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dependency)
):
    """
    Uploads an Excel file to a conversation for later use in prompts.
    """
    # Verify file type
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only .xlsx files are accepted.")
    
    # Verify conversation exists and belongs to user
    logger.info(f"User {current_user.user_id} uploading file to conversation {conversation_id}")
    conversation = crud.conversation.get_conversation_by_id(conv_id=conversation_id, user_id=current_user.user_id)
    if not conversation:
        logger.warning(f"Conversation {conversation_id} not found for user {current_user.user_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or access denied")
    
    try:
        # Create a directory for file storage if it doesn't exist
        os.makedirs(settings.USER_FILES_DIR, exist_ok=True)
        
        # Generate unique ID for the file
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.USER_FILES_DIR, f"{file_id}_{file.filename}")
        
        # Read and save the file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Process file content for RAG database
        await services.chat_service.process_excel_for_conversation(
            file_path=file_path,
            file_id=file_id,
            conversation_id=conversation_id,
            user_id=current_user.user_id,
            embedding_model=embedding_model,
            qdrant_client=qdrant_client
        )
        
        # Create file metadata
        file_metadata = FileMetadata(
            id=file_id,
            filename=file.filename,
            upload_date=datetime.datetime.now(datetime.timezone.utc),
            user_id=current_user.user_id,
            conversation_id=conversation_id
        )
        
        # Add file to conversation
        conversation.files.append(file_metadata)
        crud.conversation.save_conversation(conversation_data=conversation)
        
        logger.info(f"File {file.filename} uploaded to conversation {conversation_id} with id {file_id}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            conversation_id=conversation_id
        )
    except Exception as e:
        logger.error(f"Error uploading file to conversation {conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file: {str(e)}")
    finally:
        await file.close()

@router.get("/conversations", response_model=List[Conversation])
async def get_user_conversations_list(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieves a list of conversations for the current user.
    """
    logger.info(f"User {current_user.user_id} requesting conversation list (limit: {limit}, skip: {skip}).")
    # --- CORRECTED CALL: Use CRUD directly ---
    conversations = crud.conversation.get_user_conversations(user_id=current_user.user_id, skip=skip, limit=limit)
    # --- END CORRECTION ---
    return conversations

# Use the directly imported Conversation schema
@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_specific_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieves a specific conversation by its ID.
    """
    logger.info(f"User {current_user.user_id} requesting conversation {conversation_id}.")
    # --- CORRECTED CALL: Use CRUD directly ---
    conversation = crud.conversation.get_conversation_by_id(conv_id=conversation_id, user_id=current_user.user_id)
    # --- END CORRECTION ---
    if not conversation:
        logger.warning(f"Conversation {conversation_id} not found for user {current_user.user_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or access denied")
    return conversation

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specific_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Deletes a specific conversation by its ID.
    """
    logger.info(f"User {current_user.user_id} requesting deletion of conversation {conversation_id}.")
    # --- CORRECTED CALL: Use CRUD directly ---
    deleted = crud.conversation.delete_conversation(conv_id=conversation_id, user_id=current_user.user_id)
    # --- END CORRECTION ---
    if not deleted:
        logger.warning(f"Failed to delete conversation {conversation_id} for user {current_user.user_id} (not found or error).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or deletion failed")
    logger.info(f"Conversation {conversation_id} deleted successfully for user {current_user.user_id}.")
    return None

# Use the directly imported ChatRequest and ChatResponse schemas
@router.post("/message", response_model=ChatResponse)
async def post_chat_message(
    chat_request: ChatRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    embedding_model: SentenceTransformer = Depends(get_embedding_model_dependency),
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dependency),
    ollama_client: ollama.Client = Depends(get_ollama_client_dependency)
):
    """
    Sends a user message, gets a RAG response, and updates the conversation.
    If conversation_id is omitted, a new conversation is started.
    If file_id is included, the referenced file will be used for context.
    """
    user_id = current_user.user_id
    prompt = chat_request.prompt
    conversation_id = chat_request.conversation_id
    file_id = chat_request.file_id

    logger.info(f"User {user_id} sending message to conversation '{conversation_id or 'New'}': '{prompt[:50]}...', file_id: {file_id}")

    try:
        # 1. Handle conversation ID
        if await request.is_disconnected():
            logger.warning(f"Client disconnected before conversation handling for user {user_id}.")
            return Response(status_code=204) # Pas de contenu, le client est parti

        if not conversation_id:
            actual_new_conv = services.history_service.start_new_conversation(user_id=user_id)
            if not actual_new_conv:
                 logger.error(f"Failed to start new conversation for user {user_id} from history_service.")
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not start new conversation")
            conversation_id = actual_new_conv.id
            logger.info(f"Started new conversation {conversation_id} for user {user_id}")
        else:
             logger.info(f"Using existing conversation {conversation_id}")

        # 2. Get RAG response
        if await request.is_disconnected():
            logger.warning(f"Client disconnected before RAG processing for conversation {conversation_id}.")
            return Response(status_code=204)

        # RÃ©cupÃ©rer l'historique de conversation existant si disponible
        conversation_history = []
        current_conversation = crud.conversation.get_conversation_by_id(conv_id=conversation_id, user_id=user_id)
        if current_conversation and hasattr(current_conversation, 'messages') and current_conversation.messages:
            # Limiter l'historique aux derniers Ã©changes pour Ã©viter les prompts trop longs
            # Nous prenons les 6 derniers messages (3 Ã©changes) pour conserver le contexte rÃ©cent
            conversation_history = current_conversation.messages[-6:] if len(current_conversation.messages) > 6 else current_conversation.messages
            logger.info(f"Retrieved {len(conversation_history)} messages as conversation history.")

        file_context = None
        if file_id:
            logger.info(f"File_id '{file_id}' provided. Attempting to retrieve file context for conversation {conversation_id}.")
            try:
                file_context = services.chat_service.get_file_context(
                    file_id=file_id, 
                    query=prompt, 
                    embedding_model=embedding_model,
                    qdrant_client=qdrant_client
                )
                if file_context:
                    logger.info(f"Successfully retrieved context from file '{file_id}'. Context length: {len(file_context)}")
                else:
                    logger.warning(f"No specific context retrieved from file '{file_id}' for query '{prompt[:50]}...'. RAG will proceed without specific file context.")
            except services.chat_service.FileContextRetrievalError as e:
                logger.error(f"Error retrieving file context for file_id {file_id}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error retrieving file context for file_id {file_id}: {e}", exc_info=True)
        
        # Modifier la requÃªte pour demander une rÃ©ponse en HTML
        
        html_prompt = """IMPORTANT: Ta rÃ©ponse doit Ãªtre formatÃ©e en HTML pur, PAS en Markdown.

Formate ta rÃ©ponse avec ces balises HTML:
- <h1> pour le titre principal
- <h2> pour les sous-sections
- <h3> pour les points importants 
- <p> pour les paragraphes
- <ul><li>item</li></ul> pour les listes Ã  puces (SANS ESPACES entre les Ã©lÃ©ments)
- <ol><li>item</li></ol> pour les listes numÃ©rotÃ©es (SANS ESPACES entre les Ã©lÃ©ments)
- <strong>texte</strong> pour le gras
- <em>texte</em> pour l'italique
- <table><tr><th>entÃªte</th></tr><tr><td>cellule</td></tr></table> pour les tableaux

ATTENTION: Ã‰vite Ã  tout prix les espaces entre les Ã©lÃ©ments de liste. Format compact requis.

EXEMPLE de formatage CORRECT pour liste:
<ul>
  <li>Premier point</li>
  <li>Second point</li>
<li>TroisiÃ¨me point</li>
</ul>

Question: """ + prompt
        
        # CORRECTION: Utiliser d'abord la question originale pour la dÃ©tection, puis appliquer le HTML si nÃ©cessaire
        assistant_response_content = await services.rag_service.get_rag_response(
            user_query=prompt,  # IMPORTANT: Utiliser la question originale pour la dÃ©tection
            embedding_model=embedding_model,
            qdrant_client=qdrant_client,
            ollama_client=ollama_client,
            file_context=file_context,
            request_object=request,
            conversation_history=None,  # TEMPORAIRE: DÃ©sactiver l'historique pour rÃ©soudre le bug
            html_formatting_request=html_prompt  # Nouveau paramÃ¨tre pour le formatage HTML
        )
        assistant_message = Message(role="assistant", content=assistant_response_content)
        logger.info(f"Successfully processed RAG response for conversation {conversation_id}.")

        # 3. Save messages to history
        if await request.is_disconnected():
            logger.warning(f"Client disconnected before saving history for conversation {conversation_id}.")
            return Response(status_code=204)
        
        user_message = Message(role="user", content=prompt, file_id=file_id)
        current_conversation = crud.conversation.get_conversation_by_id(conv_id=conversation_id, user_id=user_id)
        if not current_conversation:
             logger.error(f"Failed to retrieve conversation {conversation_id} before saving history.")
        else:
            current_conversation.messages.append(user_message)
            current_conversation.messages.append(assistant_message)
            current_conversation.timestamp = datetime.datetime.now(datetime.timezone.utc)
            if len(current_conversation.messages) == 2:
                current_conversation.title = services.history_service.generate_conversation_title(current_conversation.messages)
            save_success = crud.conversation.save_conversation(conversation_data=current_conversation)
            if not save_success:
                 logger.error(f"Failed to save messages to history for conversation {conversation_id}")
            else:
                 logger.info(f"Saved messages to conversation {conversation_id}")

        # 4. Return response
        if await request.is_disconnected():
            logger.warning(f"Client disconnected just before sending final response for conversation {conversation_id}.")
            return Response(status_code=204)

        response = ChatResponse(
            conversation_id=conversation_id,
            assistant_message=assistant_message,
        )
        return response

    except ClientDisconnectedError:
        logger.warning(f"Client disconnected during processing for conversation {conversation_id} (user: {user_id}). Request processing stopped.")
        return Response(status_code=204) # RÃ©pondre avec No Content car le client est parti
    except HTTPException as http_exc:
         raise http_exc 
    except Exception as e:
         logger.error(f"[Conv: {conversation_id}] Unexpected Error in post_chat_message: {e}", exc_info=True)
         if await request.is_disconnected(): # Double check avant de lever une 500
             logger.warning(f"Client disconnected during unexpected error for conversation {conversation_id}.")
             return Response(status_code=204)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# --- NEW FEEDBACK ENDPOINT --- 
@router.post("/conversations/{conversation_id}/messages/{message_index}/feedback", 
            status_code=status.HTTP_204_NO_CONTENT)
async def submit_message_feedback(
    conversation_id: str = Path(..., description="ID of the conversation containing the message"),
    message_index: int = Path(..., ge=0, description="Index of the assistant message to provide feedback on"),
    feedback_data: FeedbackData = Body(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Submits feedback (rating and optional comment) for a specific assistant message.
    """
    logger.info(f"User {current_user.user_id} submitting feedback for conv {conversation_id}, msg index {message_index}: {feedback_data.rating}")
    
    success = crud.conversation.save_feedback_for_message(
        conv_id=conversation_id,
        user_id=current_user.user_id,
        message_index=message_index,
        feedback_data=feedback_data
    )
    
    if not success:
        conversation = crud.conversation.get_conversation_by_id(conv_id=conversation_id, user_id=current_user.user_id)
        if not conversation:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or access denied.")
        # Check index bounds *after* confirming conversation exists
        if not isinstance(conversation.messages, list) or message_index >= len(conversation.messages):
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message index out of bounds.")
        # If conversation/index is valid but saving failed, likely an internal error
        # Could also be that the message at index wasn't an assistant message (handled in CRUD)
        logger.error(f"Failed to save feedback for conv {conversation_id}, msg index {message_index}. See CRUD logs for details.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save feedback.")
    
    return None 
# --- END NEW FEEDBACK ENDPOINT ---

# --- NOUVELLE ROUTE POUR SUPPRIMER UN MESSAGE ---
@router.delete("/conversations/{conversation_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message_from_conversation(
    conversation_id: str = Path(..., description="ID de la conversation"),
    message_id: str = Path(..., description="ID du message Ã  supprimer"),
    current_user: TokenData = Depends(get_current_user)
):
    """Supprime un message spÃ©cifique (et sa rÃ©ponse assistante si applicable) d'une conversation."""
    logger.info(f"User {current_user.user_id} requesting deletion of message {message_id} from conversation {conversation_id}.")
    
    success = await crud.conversation.delete_message_in_conversation(
        conv_id=conversation_id,
        user_id=current_user.user_id,
        message_id_to_delete=message_id
    )
    
    if not success:
        # Le CRUD devrait lever une HTTPException si la conversation/message n'est pas trouvÃ©e ou si l'utilisateur n'est pas autorisÃ©.
        # Si success est false pour une autre raison, c'est une erreur serveur.
        logger.error(f"Failed to delete message {message_id} from conv {conversation_id} for user {current_user.user_id}. See CRUD logs.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete message.")
    
    logger.info(f"Message {message_id} (and potentially its pair) deleted from conversation {conversation_id}.")
    return None
# --- FIN NOUVELLE ROUTE POUR SUPPRIMER UN MESSAGE ---

# --- NEW STATISTICS ENDPOINT ---
@router.get("/statistics")
async def get_statistics(
    current_user: TokenData = Depends(get_current_user),
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dependency)
):
    try:
        # Initialiser les statistiques
        stats = {
            "data_analysis": {
                "total_flux": 0,
                "total_filiales": 0,
                "total_types_source": 0,
                "total_technologies": 0,
                "flux_par_filiale": {},
                "types_source": {},
                "plateformes": {
                    "source": {},
                    "cible": {}
                },
                "formats": {},
                "frequence_maj": {},
                "technologies": {}
            }
        }

        # RÃ©cupÃ©rer tous les points de Qdrant
        collection_name = "banque_ma_data_catalog"
        search_result = qdrant_client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )

        # Traiter les donnÃ©es
        for point in search_result[0]:
            payload = point.payload
            original_data = payload.get('original_data', {})
            source_sheet = payload.get('source_sheet')

            if source_sheet == 'RÃ©fÃ©rentiel Sources':
                # Filiale
                filiale = original_data.get('Filiale', 'Non spÃ©cifiÃ©')
                stats['data_analysis']['flux_par_filiale'][filiale] = stats['data_analysis']['flux_par_filiale'].get(filiale, 0) + 1

                # Type de source
                type_source = original_data.get('Type Source', 'Non spÃ©cifiÃ©')
                stats['data_analysis']['types_source'][type_source] = stats['data_analysis']['types_source'].get(type_source, 0) + 1

                # Plateformes
                plateforme_source = original_data.get('Plateforme source', 'Non spÃ©cifiÃ©')
                plateforme_cible = original_data.get('Plateforme cible', 'Non spÃ©cifiÃ©')
                stats['data_analysis']['plateformes']['source'][plateforme_source] = stats['data_analysis']['plateformes']['source'].get(plateforme_source, 0) + 1
                stats['data_analysis']['plateformes']['cible'][plateforme_cible] = stats['data_analysis']['plateformes']['cible'].get(plateforme_cible, 0) + 1

                # Format
                format_type = original_data.get('Format', 'Non spÃ©cifiÃ©')
                stats['data_analysis']['formats'][format_type] = stats['data_analysis']['formats'].get(format_type, 0) + 1

                # FrÃ©quence de mise Ã  jour
                frequence = original_data.get('FrÃ©quence MAJ', 'Non spÃ©cifiÃ©')
                stats['data_analysis']['frequence_maj'][frequence] = stats['data_analysis']['frequence_maj'].get(frequence, 0) + 1

                # Technologie
                technologie = original_data.get('Technologie', 'Non spÃ©cifiÃ©')
                stats['data_analysis']['technologies'][technologie] = stats['data_analysis']['technologies'].get(technologie, 0) + 1

        # Calculer les totaux
        stats['data_analysis']['total_flux'] = sum(stats['data_analysis']['flux_par_filiale'].values())
        stats['data_analysis']['total_filiales'] = len(stats['data_analysis']['flux_par_filiale'])
        stats['data_analysis']['total_types_source'] = len(stats['data_analysis']['types_source'])
        stats['data_analysis']['total_technologies'] = len(stats['data_analysis']['technologies'])

        # Calculer les pourcentages pour chaque catÃ©gorie
        def calculate_percentages(data_dict):
            total = sum(data_dict.values())
            return {k: {"count": v, "percentage": round((v / total) * 100, 2)} for k, v in data_dict.items()}

        # Appliquer le calcul des pourcentages Ã  chaque catÃ©gorie
        stats['data_analysis']['flux_par_filiale'] = calculate_percentages(stats['data_analysis']['flux_par_filiale'])
        stats['data_analysis']['types_source'] = calculate_percentages(stats['data_analysis']['types_source'])
        stats['data_analysis']['plateformes']['source'] = calculate_percentages(stats['data_analysis']['plateformes']['source'])
        stats['data_analysis']['plateformes']['cible'] = calculate_percentages(stats['data_analysis']['plateformes']['cible'])
        stats['data_analysis']['formats'] = calculate_percentages(stats['data_analysis']['formats'])
        stats['data_analysis']['frequence_maj'] = calculate_percentages(stats['data_analysis']['frequence_maj'])
        stats['data_analysis']['technologies'] = calculate_percentages(stats['data_analysis']['technologies'])

        return stats

    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VOICE CONVERSATION ENDPOINTS
# =============================================================================

@router.post("/voice/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Language code (e.g., 'en', 'fr')"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Transcribe audio file to text using OpenAI Whisper.
    
    Supports multiple audio formats: WAV, MP3, M4A, FLAC, OGG
    """
    import tempfile
    from ..services.voice_service import voice_service
    
    # Validate file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file size (limit to 25MB)
    max_size = 25 * 1024 * 1024  # 25MB
    audio_file.file.seek(0, 2)  # Seek to end
    file_size = audio_file.file.tell()
    audio_file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB")
    
    # Save uploaded file temporarily
    suffix = os.path.splitext(audio_file.filename)[1].lower()
    if suffix not in ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm']:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Transcribe audio
        result = await voice_service.transcribe_audio(temp_file_path, language)
        
        logger.info(f"User {current_user.user_id} transcribed audio: {result['text'][:100]}...")
        
        return {
            "success": True,
            "transcription": result,
            "file_info": {
                "filename": audio_file.filename,
                "size": file_size,
                "format": suffix
            }
        }
        
    except Exception as e:
        logger.error(f"Transcription failed for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass


@router.post("/voice/conversation")
async def voice_conversation(
    audio_file: UploadFile = File(..., description="Audio file with user's voice message"),
    conversation_id: Optional[str] = Form(None, description="Conversation ID to continue"),
    language: Optional[str] = Form(None, description="Language code for transcription"),
    current_user: TokenData = Depends(get_current_user),
    embedding_model: SentenceTransformer = Depends(get_embedding_model_dependency),
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dependency),
    ollama_client: ollama.Client = Depends(get_ollama_client_dependency)
):
    """
    Complete voice conversation workflow:
    1. Transcribe audio to text
    2. Process through RAG system  
    3. Return both transcription and AI response
    """
    import tempfile
    from ..services.voice_service import voice_service
    
    # Validate file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    # Check file size (limit to 25MB)
    max_size = 25 * 1024 * 1024  # 25MB
    audio_file.file.seek(0, 2)
    file_size = audio_file.file.tell()
    audio_file.file.seek(0)
    
    if file_size > max_size:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB")
    
    # Validate file format
    suffix = os.path.splitext(audio_file.filename)[1].lower()
    if suffix not in ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm']:
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process complete voice conversation
        result = await voice_service.process_voice_conversation(
            audio_file_path=temp_file_path,
            user_id=current_user.user_id,
            conversation_id=conversation_id,
            language=language,
            embedding_model=embedding_model,
            qdrant_client=qdrant_client,
            ollama_client=ollama_client
        )
        
        logger.info(f"Voice conversation completed for user {current_user.user_id}: {result['user_message'][:100]}...")
        
        return {
            "success": True,
            "user_message": result["user_message"],
            "assistant_response": result["assistant_response"],
            "conversation_id": result["conversation_id"],
            "transcription": result["transcription"],
            "metadata": result["metadata"],
            "file_info": {
                "filename": audio_file.filename,
                "size": file_size,
                "format": suffix
            }
        }
        
    except Exception as e:
        logger.error(f"Voice conversation failed for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Voice conversation failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass


@router.get("/voice/info")
async def get_voice_info(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get information about voice processing capabilities.
    """
    from ..services.voice_service import voice_service
    
    try:
        info = voice_service.get_model_info()
        languages = voice_service.get_supported_languages()
        
        return {
            "voice_processing": info,
            "supported_languages": languages,
            "examples": {
                "language_codes": ["en", "fr", "es", "de", "it", "zh", "ja"],
                "supported_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
                "max_file_size": "25MB",
                "max_duration": f"{info.get('max_duration', 300)}s"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get voice info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voice info: {str(e)}")


@router.get("/voice/languages")
async def get_supported_languages(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get list of supported languages for voice transcription.
    """
    from ..services.voice_service import voice_service
    
    try:
        languages = voice_service.get_supported_languages()
        
        # Group by common languages for better UX
        common_languages = {
            "en": "English",
            "fr": "French", 
            "es": "Spanish",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic"
        }
        
        return {
            "total_languages": len(languages),
            "common_languages": {k: languages.get(k, v) for k, v in common_languages.items() if k in languages},
            "all_languages": languages
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get languages: {str(e)}")

