# api/services/rag_service.py
import logging
from typing import List, Optional, Dict, Any
import re

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
    """Custom exception for client disconnection during processing."""
    pass

# --- Helper Functions ---

def _is_general_question(query: str) -> bool:
    """Détecte si une question est générale et n'a pas besoin de contexte RAG."""
    query_lower = query.lower().strip()
    
    # Questions de salutation
    greetings = [
        "bonjour", "salut", "hello", "hi", "bonsoir", "bonne journée",
        "comment ça va", "comment allez-vous", "ça va"
    ]
    
    # Questions sur le rôle/identité
    role_questions = [
        "qui êtes-vous", "qui es-tu", "quel est votre rôle", "quel est ton rôle",
        "que faites-vous", "que fais-tu", "à quoi servez-vous", "à quoi sers-tu",
        "comment pouvez-vous m'aider", "comment peux-tu m'aider", "pouvez-vous m'aider",
        "que puis-je vous demander", "que puis-je te demander"
    ]
    
    # Questions générales sur les capacités
    general_questions = [
        "comment ça marche", "comment ça fonctionne", "que savez-vous faire",
        "que sais-tu faire", "comment vous utilisez", "comment t'utiliser"
    ]
    
    # Remerciements
    thanks = [
        "merci", "merci beaucoup", "thank you", "thanks"
    ]
    
    # Test simple au revoir
    goodbye = [
        "au revoir", "goodbye", "bye", "à bientôt"
    ]
    
    all_general_patterns = greetings + role_questions + general_questions + thanks + goodbye
    
    # Test direct
    for pattern in all_general_patterns:
        if pattern in query_lower:
            return True
    
    # Test pour des questions très courtes (moins de 20 caractères sans termes techniques)
    if len(query_lower) < 20:
        technical_terms = [
            "compte", "client", "banque", "agence", "trésorerie", "donnée", "données",
            "fichier", "sql", "base", "flux", "registre", "limite", "crédit"
        ]
        has_technical_terms = any(term in query_lower for term in technical_terms)
        if not has_technical_terms:
            return True
    
    return False

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
    
    # LIMITE: Prendre seulement les 2 derniers messages pour éviter un prompt trop long
    # avec le modèle léger llama3.2:1b
    recent_messages = messages[-2:] if len(messages) > 2 else messages
    
    history_text = "Historique récent de la conversation:\n"
    for msg in recent_messages:
        # Vérifier si c'est un objet Pydantic (avec des attributs) ou un dictionnaire
        if hasattr(msg, 'role'):
            role = "Utilisateur" if msg.role == "user" else "Assistant"
            content = msg.content
        else:
            # Fallback pour les dictionnaires (au cas où)
            role = "Utilisateur" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
        
        # Limiter aussi la longueur de chaque message à 200 caractères max
        if len(content) > 200:
            content = content[:200] + "..."
        
        history_text += f"{role}: {content}\n\n"
    
    return history_text

async def _generate_response(query: str, context_chunks: List[str], ollama_client: ollama.AsyncClient, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Generates a response using the Ollama LLM with context, forcing French output."""
    if not context_chunks:
        context_string = "Aucun contexte pertinent trouvé." # Context notice in French
    else:
        # OPTIMISATION AGRESSIVE pour modèle léger llama3.2:1b
        max_chunks = 8 if conversation_history else 10  # Réduction drastique
        limited_chunks = context_chunks[:max_chunks]
        
        # Limiter drastiquement la longueur de chaque chunk à 150 caractères max
        truncated_chunks = []
        for chunk in limited_chunks:
            if len(chunk) > 150:
                truncated_chunks.append(chunk[:150] + "...")
            else:
                truncated_chunks.append(chunk)
        
        context_string = "\n---\n".join(truncated_chunks)

    # Format conversation history if provided - VERSION ULTRA COURTE
    history_string = ""
    if conversation_history:
        # Prendre seulement le DERNIER message pour éviter un prompt trop long
        recent_messages = conversation_history[-1:] if conversation_history else []
        
        if recent_messages:
            msg = recent_messages[0]
            if hasattr(msg, 'role'):
                role = "U" if msg.role == "user" else "A"  # Ultra court
                content = msg.content
            else:
                role = "U" if msg.get("role") == "user" else "A"
                content = msg.get("content", "")
            
            # Limiter à 100 caractères max
            if len(content) > 100:
                content = content[:100] + "..."
                
            history_string = f"Dernier: {role}: {content}\n"
        
        logger.info(f"Including conversation history with {len(conversation_history)} messages")
    
    # PROMPT ULTRA SIMPLIFIÉ pour modèle léger
    prompt = f"""Assistant bancaire Banque Populaire. Français uniquement.

{history_string}
CONTEXTE:
{context_string}

Q: {query}
R:"""

    # End of improved prompt

    logger.info(f"Sending request to Ollama model: {settings.OLLAMA_MODEL_NAME}...")
    logger.info(f"Prompt length: {len(prompt)} characters")

    try:
        # Timeouts encore plus agressifs
        if len(prompt) > 2000:  # Prompt long
            request_timeout = 180  # 3 minutes max
            logger.warning(f"Large prompt detected ({len(prompt)} chars). Using extended timeout.")
        elif len(prompt) > 1000:  # Prompt moyen
            request_timeout = 90   # 1.5 minutes
        else:  # Prompt court
            request_timeout = 45   # 45 secondes
            
        logger.info(f"Using optimized timeout of {request_timeout} seconds for Ollama request")
        
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
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    html_formatting_request: Optional[str] = None
) -> str:
    """
    Generates a response using Retrieval-Augmented Generation.
    If file_context is provided, it prioritizes it and skips the general search.
    If conversation_history is provided, includes it for context.
    If html_formatting_request is provided, uses it for technical questions that need HTML formatting.
    Raises specific exceptions on failure.
    Checks for client disconnection if request_object is provided.
    """
    logger.info(f"RAG Service: Processing query '{user_query[:50]}...'")

    if request_object and await request_object.is_disconnected():
        logger.warning("Client disconnected before RAG processing started.")
        raise ClientDisconnectedError()

    # Détecter les questions générales et y répondre directement
    if _is_general_question(user_query):
        logger.info("General question detected. Providing direct response without RAG.")
        return await _generate_general_response(user_query, ollama_client)

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
    
    # Pour les questions techniques, utiliser le formatage HTML si demandé
    final_query = html_formatting_request if html_formatting_request else user_query
    
    assistant_response = await _generate_response(
        query=final_query, 
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

async def _generate_general_response(query: str, ollama_client: ollama.AsyncClient) -> str:
    """Génère une réponse appropriée pour les questions générales sans contexte RAG."""
    query_lower = query.lower().strip()
    
    # Réponses prédéfinies pour des cas courants
    if any(greeting in query_lower for greeting in ["bonjour", "salut", "hello", "hi", "bonsoir"]):
        return "Bonjour ! Je suis votre assistant virtuel de la Banque Populaire. Je peux vous aider à analyser vos données bancaires, répondre à vos questions sur les comptes et les opérations. Comment puis-je vous assister aujourd'hui ?"
    
    if any(role in query_lower for role in ["rôle", "qui êtes-vous", "qui es-tu", "que faites-vous"]):
        return "Je suis l'assistant virtuel de la Banque Populaire, spécialisé dans l'analyse de données bancaires. Je peux vous aider à :\n\n• Analyser vos fichiers de données\n• Comprendre les structures de comptes\n• Interpréter les flux financiers\n• Répondre aux questions sur les opérations bancaires\n\nPosez-moi une question spécifique sur vos données !"
    
    if any(help_term in query_lower for help_term in ["comment m'aider", "que puis-je demander", "capacités"]):
        return "Je peux vous assister sur plusieurs aspects :\n\n• **Analyse de fichiers** : Téléversez vos données Excel/CSV\n• **Questions techniques** : Formats, champs, structures\n• **Interprétation** : Flux, comptes, opérations\n• **Aide métier** : Processus bancaires, terminologie\n\nCommencez par me poser une question ou téléverser un fichier à analyser !"
    
    if any(thanks in query_lower for thanks in ["merci", "thank you"]):
        return "Je vous en prie ! N'hésitez pas si vous avez d'autres questions sur vos données bancaires."
    
    if any(goodbye in query_lower for goodbye in ["au revoir", "goodbye", "bye"]):
        return "Au revoir ! À bientôt pour vos prochaines analyses de données."
    
    # Pour les autres questions générales, utiliser le LLM avec un prompt simple
    simple_prompt = f"""Tu es l'assistant virtuel de la Banque Populaire. Réponds de manière professionnelle et concise à cette question générale (sans données spécifiques) : {query}

Garde un ton professionnel et oriente vers les services d'analyse de données si pertinent."""
    
    try:
        response = await ollama_client.chat(
            model=settings.OLLAMA_MODEL_NAME,
            messages=[{'role': 'user', 'content': simple_prompt}]
        )
        if response and 'message' in response and 'content' in response['message']:
            return response['message']['content'].strip()
        else:
            return "Je suis là pour vous aider avec vos questions bancaires. Pouvez-vous reformuler votre demande ?"
    except Exception as e:
        logger.error(f"Error generating general response: {e}")
        return "Je suis votre assistant Banque Populaire. Comment puis-je vous aider avec vos données bancaires ?"