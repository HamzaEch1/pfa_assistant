# api/services/rag_service.py
import logging
from typing import List, Optional, Dict, Any

import ollama
import httpx # Import httpx to catch potential timeout errors specifically
from fastapi import Request
from qdrant_client import QdrantClient, models as qdrant_models
from qdrant_client.http.models import PointStruct
from sentence_transformers import SentenceTransformer

# Use relative import to get settings
# Assuming your config file is correctly located relative to this service
# If rag_service.py is inside 'services' which is inside 'api',
# and config.py is inside 'core' which is inside 'api':
from ..core.config import settings
# If the structure is different, adjust the relative import path accordingly.

logger = logging.getLogger(__name__)

# --- Custom Exceptions ---
class RagEmbeddingError(Exception):
    """Custom exception for embedding failures."""
    pass

class RagSearchError(Exception):
    """Custom exception for vector search failures."""
    pass

class RagGenerationError(Exception):
    """Custom exception for LLM generation failures."""
    pass

class ClientDisconnectedError(Exception):
    """Custom exception for when the client has disconnected."""
    pass

# --- Helper Functions ---

def _get_embedding(query: str, embedding_model: SentenceTransformer) -> List[float]:
    """Generates embedding for the query."""
    try:
        logger.info("Generating embedding for query...")
        embedding = embedding_model.encode(query).tolist()
        logger.info("Embedding generated successfully.")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}", exc_info=True)
        raise RagEmbeddingError(f"Failed to generate embedding: {e}")

def _search_qdrant(query_embedding: List[float], qdrant_client: QdrantClient, query_text: str = "") -> List[str]:
    """Searches Qdrant for relevant context."""
    try:
        logger.info(f"Searching Qdrant collection '{settings.QDRANT_COLLECTION_NAME}'...")
        
        # Extraire les termes clés de la requête pour affiner la recherche
        important_terms = []
        if query_text:
            # Extraire les termes entre guillemets qui sont souvent importants
            import re
            quoted_terms = re.findall(r'"([^"]*)"', query_text)
            for term in quoted_terms:
                important_terms.append(term)
            
            # Extraire les noms de champs potentiels (par exemple, mots en majuscules avec underscores)
            # Regex: [A-Z_][A-Z0-9_]*  (mot commençant par majuscule ou _, suivi de majuscules, chiffres, ou _)
            field_name_pattern = r'\b[A-Z_][A-Z0-9_]*\b'
            potential_field_names = re.findall(field_name_pattern, query_text) 
            for field_name in potential_field_names:
                # Éviter d'ajouter des mots très courts ou des acronymes génériques si non pertinents
                if len(field_name) > 2 and field_name not in important_terms: # Simple filtre
                    important_terms.append(field_name)
            
            # Identifier les mots-clés potentiels (filiales, domaines, etc.)
            potential_keywords = [
                "filiale", "agence", "domaine", "Trésorerie", "BankMA", "compte",
                "libellé métier", "terme métier"
            ]
            for keyword in potential_keywords:
                if keyword.lower() in query_text.lower():
                    important_terms.append(keyword)
        
        logger.info(f"Identified important search terms: {important_terms}")
        
        # Recherche vectorielle standard
        search_result = qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=settings.NUM_RESULTS_TO_RETRIEVE * 2,  # On récupère plus de résultats pour filtrer après
        )
        
        # Filtrer et trier les résultats par pertinence
        filtered_results = []
        for hit in search_result:
            if not hit.payload or "text" not in hit.payload:
                continue
                
            text = hit.payload.get("text", "")
            
            # Calculer un score de pertinence basé sur les termes importants
            relevance_score = hit.score  # Score vectoriel de base
            
            # Augmenter le score si le texte contient des termes importants
            for term in important_terms:
                if term.lower() in text.lower():
                    relevance_score += 0.1  # Bonus pour chaque terme important présent
            
            filtered_results.append((text, relevance_score))
        
        # Trier par score de pertinence
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        
        # Prendre uniquement les meilleurs résultats
        top_results = filtered_results[:settings.NUM_RESULTS_TO_RETRIEVE]
        
        # Extraire uniquement les textes
        context_chunks = [text for text, _ in top_results]
        
        logger.info(f"Retrieved {len(context_chunks)} relevant text chunks from Qdrant.")
        if not context_chunks:
            logger.warning("No relevant context chunks found in Qdrant.")
        return context_chunks
    except Exception as e:
        logger.error(f"Failed to search Qdrant: {e}", exc_info=True)
        raise RagSearchError(f"Failed to search Qdrant: {e}")

def _format_conversation_history(messages: List[Dict[str, Any]]) -> str:
    """Format the conversation history for inclusion in the prompt."""
    if not messages:
        return ""
    
    history_text = "Historique de la conversation:\n"
    for msg in messages:
        # Vérifier si c'est un objet Pydantic (avec des attributs) ou un dictionnaire
        if hasattr(msg, 'role'):
            role = "Utilisateur" if msg.role == "user" else "Assistant"
            content = msg.content
        else:
            # Fallback pour les dictionnaires (au cas où)
            role = "Utilisateur" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
        
        history_text += f"{role}: {content}\n\n"
    
    return history_text

async def _generate_response(query: str, context_chunks: List[str], ollama_client: ollama.AsyncClient, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Generates a response using the Ollama LLM with context, forcing French output."""
    if not context_chunks:
        context_string = "Aucun contexte pertinent trouvé." # Context notice in French
    else:
        context_string = "\n---\n".join(context_chunks)

    # Format conversation history if provided
    history_string = ""
    if conversation_history:
        history_string = _format_conversation_history(conversation_history)
        logger.info(f"Including conversation history with {len(conversation_history)} messages")
    
    # IMPROVED PROMPT FOR BETTER RESPONSES
    prompt = f"""
Tu es un assistant bancaire expert dans l'analyse de données pour Banque Populaire. 
Ta mission est de fournir des réponses précises et pertinentes en te basant UNIQUEMENT sur les informations du contexte fourni.

DIRECTIVES IMPORTANTES:
1. Si le contexte ne contient pas d'information spécifique à la question, dis-le clairement: "Je ne dispose pas d'informations sur [sujet] dans mes données actuelles." 
2. Ne tente jamais de deviner ou d'inventer des informations qui ne sont pas présentes dans le contexte.
3. Sois précis et factuel dans tes réponses.
4. Réponds UNIQUEMENT en français.
5. Si la question mentionne une filiale, un domaine ou un champ spécifique, concentre-toi uniquement sur les informations relatives à ces éléments.
6. Lorsque la question utilise des pronoms (par exemple 'il', 'elle', 'ceci', 'cela'), utilise l'historique de la conversation et plus précisement le dernier message pour déterminer à quoi le pronom se réfère. Ta réponse doit être pertinente par rapport au sujet identifié dans l'historique. Si le sujet n'est pas clair malgré l'historique, indique que le sujet de la question est ambigu.

{history_string}

CONTEXTE:
---
{context_string}
---

QUESTION: {query}

Réponse claire et précise:
"""
    # End of improved prompt

    logger.info(f"Sending request to Ollama model: {settings.OLLAMA_MODEL_NAME}...")
    # logger.debug(f"Full prompt sent to Ollama:\n{prompt}") # Optional: Uncomment to log full prompt

    try:
        # Use a specific higher timeout for this request, overriding client default
        request_timeout = settings.OLLAMA_CLIENT_TIMEOUT
        if len(prompt) > 2000:  # If prompt is large, increase timeout
            request_timeout = max(request_timeout, 900)  # 15 minutes max for large prompts
            
        logger.info(f"Using request timeout of {request_timeout} seconds for Ollama request")
        
        # Note: ollama.Client timeout is set during initialization elsewhere (e.g., models.py or main app setup)
        response = await ollama_client.chat(
            model=settings.OLLAMA_MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}]
            # Removed timeout and keep_alive arguments as they are not supported
            # stream=False, # Keep stream False if you expect the full response object
        )
        logger.info("Received response from Ollama.")

        if response and 'message' in response and 'content' in response['message']:
             assistant_content = response['message']['content'].strip()
             # Optional: Add basic response validation/filtering here if needed
             if not assistant_content:
                 logger.warning("Ollama returned an empty response content.")
                 # Return an error message also in French, if desired
                 return "Désolé, je n'ai pas pu générer de réponse."
             logger.info("Extracted content from Ollama response.")
             return assistant_content
        else:
            logger.error(f"Unexpected response structure from Ollama: {response}")
            # Keep exception message in English for dev clarity, or change if needed
            raise RagGenerationError("Received unexpected response structure from the language model.")

    except httpx.TimeoutException as e:
        logger.error(f"Timeout error connecting to Ollama: {e}", exc_info=True)
        # Keep exception message in English for dev clarity, or change if needed
        raise RagGenerationError(f"Request to language model timed out: {e}")
    except ollama.ResponseError as e:
         # Handle specific Ollama errors
         logger.error(f"Ollama API error: {e.error} (Status: {e.status_code})", exc_info=True)
         # Keep exception message in English for dev clarity, or change if needed
         raise RagGenerationError(f"Language model API error: {e.error}")
    except Exception as e:
        logger.error(f"Failed to get response from Ollama: {e}", exc_info=True)
        # Keep exception message in English for dev clarity, or change if needed
        raise RagGenerationError(f"Failed to get response from language model: {e}")

# --- Main Service Function ---

async def get_rag_response(
    user_query: str,
    embedding_model: SentenceTransformer,
    qdrant_client: QdrantClient,
    ollama_client: ollama.AsyncClient,
    file_context: Optional[str] = None,
    request_object: Optional[Request] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Generates a response using Retrieval-Augmented Generation.
    If file_context is provided, it prioritizes it and skips the general search.
    If conversation_history is provided, includes it for context.
    Raises specific exceptions on failure.
    Checks for client disconnection if request_object is provided.
    """
    logger.info(f"RAG Service: Processing query '{user_query[:50]}...'")

    if request_object and await request_object.is_disconnected():
        logger.warning("Client disconnected before RAG processing started.")
        raise ClientDisconnectedError()

    query_embedding = _get_embedding(user_query, embedding_model)

    if request_object and await request_object.is_disconnected():
        logger.warning("Client disconnected after embedding generation.")
        raise ClientDisconnectedError()

    context_chunks = []
    if file_context:
        logger.info("File context provided. Using it as primary context and skipping general search.")
        file_context_chunk = f"CONTENU DU FICHIER TÉLÉVERSÉ:\n---\n{file_context}\n---"
        context_chunks = [file_context_chunk]
    else:
        logger.info("No file context provided. Searching general Qdrant collection.")
        context_chunks = _search_qdrant(query_embedding, qdrant_client, user_query)

    if request_object and await request_object.is_disconnected():
        logger.warning("Client disconnected after context retrieval.")
        raise ClientDisconnectedError()
    
    assistant_response = await _generate_response(
        query=user_query, 
        context_chunks=context_chunks, 
        ollama_client=ollama_client,
        conversation_history=conversation_history
    )

    if request_object and await request_object.is_disconnected():
        logger.warning("Client disconnected after Ollama response generation (but response was generated).")
        # La réponse est générée, mais le client est parti. On pourrait quand même logger/stocker la réponse.
        raise ClientDisconnectedError()

    logger.info("RAG Service: Successfully generated response based on provided context and conversation history.")
    return assistant_response