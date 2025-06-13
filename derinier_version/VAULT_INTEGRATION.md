# HashiCorp Vault Integration

This document describes how the application integrates with HashiCorp Vault for secret management.

## Overview

[HashiCorp Vault](https://www.vaultproject.io/) is used to securely store and manage sensitive information such as:
- Database credentials
- API keys
- JWT authentication secrets
- Service configuration

## Setup

### Quick Start

To start the application with Vault integration:

```bash
./start-with-vault.sh
```

This script will:
1. Start all services including Vault
2. Initialize Vault with default policies and secrets
3. Configure the API to use Vault for secret management

### Manual Setup

If you prefer to set up Vault manually:

1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. Initialize Vault:
   ```bash
   ./vault/setup_vault.sh
   ```

3. Load the generated credentials:
   ```bash
   source api_vault_credentials.env
   ```

## Vault UI

Once running, you can access the Vault UI at:
```
http://localhost:8200/ui
```

Use the root token from your `.env` file or the default value (`myroot`) to log in.

## Secret Management

### Secret Paths

Secrets are organized in the following paths:

- `kv/api/db` - Database credentials
- `kv/api/jwt` - JWT authentication configuration
- `kv/api/qdrant` - Qdrant vector database configuration
- `kv/api/ollama` - Ollama LLM configuration
- `kv/api/embedding` - Embedding model configuration

### Adding New Secrets

To add a new secret:

1. Access the Vault UI or use the CLI:
   ```bash
   export VAULT_ADDR=http://localhost:8200
   export VAULT_TOKEN=myroot  # or your actual token
   ```

2. Create or update a secret:
   ```bash
   vault kv put kv/api/my-new-secret key1=value1 key2=value2
   ```

3. To read a secret:
   ```bash
   vault kv get kv/api/my-new-secret
   ```

## Application Integration

The application uses the following components for Vault integration:

1. `api/core/vault.py` - Vault client for retrieving secrets
2. `api/core/config.py` - Settings with Vault integration

### Using Secrets in Code

To use secrets in your code:

```python
from api.core.vault import get_vault_client

# Get Vault client
vault_client = get_vault_client()

# Retrieve a secret
my_secret = vault_client.get_secret('api/my-new-secret')

# Use the secret
value1 = my_secret.get('key1')
```

## Production Considerations

For production environments:

1. Use proper Vault authentication methods (not the root token)
2. Enable audit logging
3. Use proper access control policies
4. Consider using a highly available Vault cluster
5. Implement proper seal/unseal procedures
6. Set up automatic secret rotation

## Troubleshooting

1. **API can't connect to Vault**
   - Check that the `VAULT_ADDR` environment variable is correct
   - Verify that Vault is running and healthy
   - Check that the Role ID and Secret ID are correctly set

2. **Permission denied errors**
   - Verify that the policy allows access to the required paths
   - Check that the AppRole has the correct policy attached

3. **Vault is sealed**
   - In development mode, Vault auto-unseals
   - In production, follow proper unseal procedures 