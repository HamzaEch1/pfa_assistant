# api/core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Using pydantic-settings for better validation and type hints
class Settings(BaseSettings):
    # Page Configuration
    PAGE_TITLE: str = "Chat Banque Populaire"
    PAGE_ICON: str = "https://www.zonebourse.com/static/private-issuer-squared-9I42B.png"

    # Vault Configuration
    VAULT_ENABLED: bool = os.getenv("VAULT_ENABLED", "false").lower() == "true"
    VAULT_ADDR: str = os.getenv("VAULT_ADDR", "http://vault:8200")
    
    # External Services Configuration - These will be overridden by Vault if enabled
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "banque_ma_data_catalog")
    QDRANT_CLIENT_TIMEOUT: int = int(os.getenv("QDRANT_CLIENT_TIMEOUT", "20")) # Timeout for Qdrant client operations (seconds)

    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", 'paraphrase-multilingual-MiniLM-L12-v2')
    # Optional: Add TRANSFORMERS_CACHE=/path/in/container if needed

    OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL_NAME", "llama3:8b") # Defaulting to the likely correct quantized tag
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    OLLAMA_CLIENT_TIMEOUT: int = int(os.getenv("OLLAMA_CLIENT_TIMEOUT", "600")) # Timeout for Ollama client operations (seconds)

    NUM_RESULTS_TO_RETRIEVE: int = int(os.getenv("NUM_RESULTS_TO_RETRIEVE", 18))

    # User Files Configuration
    USER_FILES_DIR: str = os.getenv("USER_FILES_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_files"))

    # PostgreSQL Configuration
    PG_HOST: str = os.getenv("PG_HOST", "db")
    PG_PORT: str = os.getenv("PG_PORT", "5432")
    PG_USER: str = os.getenv("PG_USER", "user")
    PG_PASSWORD: str = os.getenv("PG_PASSWORD", "password")
    PG_DB: str = os.getenv("PG_DB", "mydb")
    DATABASE_URL: str = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default-insecure-secret-key-for-dev-only")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXP_DELTA_SECONDS: int = 3600 # 1h

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    logger.info("Loading application settings...")
    settings_instance = Settings()
    
    # Try to use Vault for secrets if enabled
    if settings_instance.VAULT_ENABLED:
        try:
            from .vault import get_vault_client
            logger.info("Vault is enabled, retrieving secrets from Vault...")
            
            vault_client = get_vault_client()
            
            # Retrieve DB config from Vault
            db_config = vault_client.get_db_config()
            if db_config:
                settings_instance.PG_HOST = db_config.get('host', settings_instance.PG_HOST)
                settings_instance.PG_PORT = db_config.get('port', settings_instance.PG_PORT)
                settings_instance.PG_USER = db_config.get('user', settings_instance.PG_USER)
                settings_instance.PG_PASSWORD = db_config.get('password', settings_instance.PG_PASSWORD)
                settings_instance.PG_DB = db_config.get('dbname', settings_instance.PG_DB)
                settings_instance.DATABASE_URL = f"postgresql://{settings_instance.PG_USER}:{settings_instance.PG_PASSWORD}@{settings_instance.PG_HOST}:{settings_instance.PG_PORT}/{settings_instance.PG_DB}"
            
            # Retrieve JWT config from Vault
            jwt_config = vault_client.get_jwt_config()
            if jwt_config:
                settings_instance.JWT_SECRET_KEY = jwt_config.get('secret_key', settings_instance.JWT_SECRET_KEY)
                settings_instance.JWT_ALGORITHM = jwt_config.get('algorithm', settings_instance.JWT_ALGORITHM)
                settings_instance.JWT_EXP_DELTA_SECONDS = int(jwt_config.get('exp_delta_seconds', settings_instance.JWT_EXP_DELTA_SECONDS))
            
            # Retrieve Qdrant config from Vault
            qdrant_config = vault_client.get_qdrant_config()
            if qdrant_config:
                settings_instance.QDRANT_URL = qdrant_config.get('url', settings_instance.QDRANT_URL)
                settings_instance.QDRANT_COLLECTION_NAME = qdrant_config.get('collection_name', settings_instance.QDRANT_COLLECTION_NAME)
                settings_instance.QDRANT_CLIENT_TIMEOUT = int(qdrant_config.get('client_timeout', settings_instance.QDRANT_CLIENT_TIMEOUT))
            
            # Retrieve Ollama config from Vault
            ollama_config = vault_client.get_ollama_config()
            if ollama_config:
                settings_instance.OLLAMA_HOST = ollama_config.get('host', settings_instance.OLLAMA_HOST)
                settings_instance.OLLAMA_MODEL_NAME = ollama_config.get('model_name', settings_instance.OLLAMA_MODEL_NAME)
                settings_instance.OLLAMA_CLIENT_TIMEOUT = int(ollama_config.get('client_timeout', settings_instance.OLLAMA_CLIENT_TIMEOUT))
            
            # Retrieve Embedding config from Vault
            embedding_config = vault_client.get_embedding_config()
            if embedding_config:
                settings_instance.EMBEDDING_MODEL_NAME = embedding_config.get('model_name', settings_instance.EMBEDDING_MODEL_NAME)
            
            logger.info("Successfully loaded secrets from Vault")
            
        except Exception as e:
            logger.error(f"Error retrieving secrets from Vault: {str(e)}. Falling back to environment variables.")
    
    if settings_instance.JWT_SECRET_KEY == "default-insecure-secret-key-for-dev-only":
         logger.warning("\nALERT: Using default insecure JWT_SECRET_KEY. Set the JWT_SECRET_KEY environment variable for production!\n")
    
    # Ensure user files directory exists
    os.makedirs(settings_instance.USER_FILES_DIR, exist_ok=True)

    # Log the settings (excluding sensitive information)
    logger.info(f"Using Qdrant URL: {settings_instance.QDRANT_URL}")
    logger.info(f"Using Qdrant Collection: {settings_instance.QDRANT_COLLECTION_NAME}")
    logger.info(f"Using Embedding Model: {settings_instance.EMBEDDING_MODEL_NAME}")
    logger.info(f"Using Ollama Host: {settings_instance.OLLAMA_HOST}")
    logger.info(f"Using Ollama Model: {settings_instance.OLLAMA_MODEL_NAME}")
    logger.info(f"User files directory: {settings_instance.USER_FILES_DIR}")

    return settings_instance

settings = get_settings()