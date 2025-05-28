# api/core/models.py
import logging
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import ollama
import httpx # Import httpx to catch potential timeout errors specifically
import json
import asyncio # Added for asyncio.Lock

# Use relative import to get settings
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Embedding Model ---
@lru_cache()
def get_embedding_model() -> SentenceTransformer | None:
    """Loads the Sentence Transformer model, logging errors."""
    model_name = settings.EMBEDDING_MODEL_NAME
    logger.info(f"Attempting to load embedding model: {model_name}")
    try:
        # Specify cache directory explicitly if needed, otherwise uses default
        # cache_folder = settings.TRANSFORMERS_CACHE # Example if you add this setting
        model = SentenceTransformer(model_name) # cache_folder=cache_folder)
        logger.info(f"Embedding model '{model_name}' loaded successfully.")
        return model
    except ImportError:
        logger.critical("SentenceTransformers library not found. Please install it: pip install sentence-transformers", exc_info=True)
        return None
    except Exception as e:
        # Log the full error during loading
        logger.critical(f"CRITICAL Error loading embedding model '{model_name}': {e}", exc_info=True)
        return None

# --- Qdrant Client ---
@lru_cache()
def get_qdrant_client() -> QdrantClient | None:
    """Connects to the Qdrant vector database with logging."""
    qdrant_url = settings.QDRANT_URL
    collection_name = settings.QDRANT_COLLECTION_NAME
    qdrant_timeout = settings.QDRANT_CLIENT_TIMEOUT # Use setting from config
    logger.info(f"Attempting connection to Qdrant at {qdrant_url} (timeout: {qdrant_timeout}s)...")
    try:
        client = QdrantClient(url=qdrant_url, timeout=qdrant_timeout) # Use configured timeout
        # Check connection by getting collection info
        client.get_collection(collection_name=collection_name)
        logger.info(f"Connected to Qdrant and verified collection '{collection_name}'.")
        return client
    except Exception as e:
        logger.critical(f"CRITICAL Error connecting to Qdrant ({qdrant_url}) or verifying collection '{collection_name}': {e}", exc_info=True)
        return None

# --- Ollama Client ---
_ollama_async_client: ollama.AsyncClient | None = None
_ollama_client_lock = asyncio.Lock()

async def get_ollama_client() -> ollama.AsyncClient | None:
    """Connects to the Ollama async client with configurable timeout and logging.
    Ensures the client is initialized only once.
    """
    global _ollama_async_client
    if _ollama_async_client is None:
        async with _ollama_client_lock:
            # Double-check after acquiring the lock
            if _ollama_async_client is None:
                ollama_host = settings.OLLAMA_HOST
                ollama_timeout = settings.OLLAMA_CLIENT_TIMEOUT
                logger.info(f"Attempting connection to Ollama (async client) at {ollama_host} (timeout: {ollama_timeout}s)...")
                try:
                    client_instance = ollama.AsyncClient(host=ollama_host, timeout=ollama_timeout)
                    await client_instance.list()  # Test connection
                    logger.info("Connected to Ollama (async client) successfully.")
                    _ollama_async_client = client_instance
                except ImportError:
                    logger.critical("Ollama library not found. Install it: pip install ollama", exc_info=True)
                    # _ollama_async_client remains None
                except (httpx.TimeoutException, ollama.ResponseError) as e:
                    logger.critical(f"CRITICAL Error connecting to Ollama (async client) ({ollama_host}) during initial check: {e}", exc_info=True)
                    # _ollama_async_client remains None
                except Exception as e:
                    logger.critical(f"CRITICAL Unexpected error connecting to Ollama (async client) ({ollama_host}): {e}", exc_info=True)
                    # _ollama_async_client remains None
    return _ollama_async_client

async def get_ollama_client_dependency() -> ollama.AsyncClient:
    """Dependency function to get the Ollama async client."""
    client = await get_ollama_client() # This is line 38 in your traceback
    if client is None:
        logger.critical("Ollama async client dependency not available.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM async client is not available")
    return client