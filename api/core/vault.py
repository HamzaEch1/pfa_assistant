# api/core/vault.py
import os
import hvac
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

class VaultClient:
    """Client for interacting with HashiCorp Vault."""
    
    def __init__(self):
        """Initialize the Vault client using AppRole authentication."""
        self.vault_addr = os.getenv("VAULT_ADDR", "http://vault:8200")
        self.role_id = os.getenv("VAULT_ROLE_ID")
        self.secret_id = os.getenv("VAULT_SECRET_ID")
        
        # For development/testing with dev server
        self.dev_root_token = os.getenv("VAULT_DEV_ROOT_TOKEN_ID")
        
        self.client = hvac.Client(url=self.vault_addr)
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Vault using AppRole or token."""
        try:
            if self.role_id and self.secret_id:
                logger.info("Authenticating to Vault using AppRole...")
                self.client.auth.approle.login(
                    role_id=self.role_id,
                    secret_id=self.secret_id
                )
            elif self.dev_root_token:
                logger.warning("Using root token for Vault authentication (DEVELOPMENT ONLY)")
                self.client.token = self.dev_root_token
            else:
                logger.error("No Vault authentication method available")
                raise ValueError("No Vault authentication method available")
                
            if not self.client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")
                
            logger.info("Successfully authenticated with Vault")
            
        except Exception as e:
            logger.error(f"Error authenticating with Vault: {str(e)}")
            raise
    
    def get_secret(self, path, key=None):
        """
        Retrieve a secret from Vault's KV v2 engine.
        
        Args:
            path (str): Path to the secret, e.g., 'api/db'
            key (str, optional): Specific key to retrieve. If None, returns all keys.
            
        Returns:
            The secret value or dictionary of values.
        """
        try:
            # Path for KV v2 requires 'data/' prefix
            full_path = f"kv/data/{path}"
            
            # Get the secret
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point="kv"
            )
            
            # Extract the data
            if not response or 'data' not in response or 'data' not in response['data']:
                logger.error(f"No data found at {path}")
                return None
                
            data = response['data']['data']
            
            # Return specific key or all data
            if key and key in data:
                return data[key]
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving secret {path}: {str(e)}")
            return None
    
    def get_db_config(self):
        """Get database configuration from Vault."""
        return self.get_secret('api/db')
    
    def get_jwt_config(self):
        """Get JWT configuration from Vault."""
        return self.get_secret('api/jwt')
    
    def get_qdrant_config(self):
        """Get Qdrant configuration from Vault."""
        return self.get_secret('api/qdrant')
    
    def get_ollama_config(self):
        """Get Ollama configuration from Vault."""
        return self.get_secret('api/ollama')
    
    def get_embedding_config(self):
        """Get embedding model configuration from Vault."""
        return self.get_secret('api/embedding')

@lru_cache()
def get_vault_client():
    """Get or create a VaultClient instance (cached)."""
    logger.info("Initializing Vault client...")
    return VaultClient() 