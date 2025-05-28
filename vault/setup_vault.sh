#!/bin/bash
set -e

# Default values
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN_ID:-myroot}"

echo "Setting up HashiCorp Vault at $VAULT_ADDR"

# Wait for Vault to be ready
until curl -s -o /dev/null -w "%{http_code}" $VAULT_ADDR/v1/sys/health | grep -q "200\|429"; do
  echo "Waiting for Vault to start..."
  sleep 2
done

# Set the Vault token for authentication
export VAULT_TOKEN

# Create and configure a KV version 2 secrets engine
echo "Enabling KV secrets engine..."
vault secrets enable -version=2 kv

# Create a policy for the API to read secrets
echo "Creating API policy..."
vault policy write api-policy - << EOF
path "kv/data/api/*" {
  capabilities = ["read"]
}
EOF

# Create an AppRole for the API service
echo "Creating AppRole for API service..."
vault auth enable approle
vault write auth/approle/role/api-role \
  secret_id_ttl=0 \
  token_num_uses=0 \
  token_ttl=24h \
  token_max_ttl=720h \
  secret_id_num_uses=0 \
  policies=api-policy

# Get role-id and secret-id for the API service
ROLE_ID=$(vault read -format=json auth/approle/role/api-role/role-id | jq -r .data.role_id)
SECRET_ID=$(vault write -format=json -f auth/approle/role/api-role/secret-id | jq -r .data.secret_id)

echo "Role ID: $ROLE_ID"
echo "Secret ID: $SECRET_ID"

# Store these in a file for the API service to use
echo "VAULT_ROLE_ID=$ROLE_ID" > api_vault_credentials.env
echo "VAULT_SECRET_ID=$SECRET_ID" >> api_vault_credentials.env

# Store secrets in Vault
echo "Storing secrets in Vault..."

# PostgreSQL credentials
vault kv put kv/api/db \
  host="${PG_HOST:-db}" \
  port="${PG_PORT:-5432}" \
  user="${PG_USER:-user}" \
  password="${PG_PASSWORD:-password}" \
  dbname="${PG_DB:-mydb}"

# JWT secret
vault kv put kv/api/jwt \
  secret_key="${JWT_SECRET_KEY:-secure-jwt-key-for-production}" \
  algorithm="HS256" \
  exp_delta_seconds="3600"

# Qdrant configuration
vault kv put kv/api/qdrant \
  url="${QDRANT_URL:-http://qdrant:6333}" \
  collection_name="${QDRANT_COLLECTION_NAME:-banque_ma_data_catalog}" \
  client_timeout="${QDRANT_CLIENT_TIMEOUT:-120}"

# Ollama configuration
vault kv put kv/api/ollama \
  host="${OLLAMA_HOST:-http://172.17.0.1:11434}" \
  model_name="${OLLAMA_MODEL_NAME:-llama3:8b}" \
  client_timeout="${OLLAMA_CLIENT_TIMEOUT:-12000}"

# Embedding model configuration
vault kv put kv/api/embedding \
  model_name="${EMBEDDING_MODEL_NAME:-paraphrase-multilingual-MiniLM-L12-v2}"

echo "Vault setup complete!"
echo "API credentials saved to api_vault_credentials.env" 