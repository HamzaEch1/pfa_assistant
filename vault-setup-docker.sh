#!/bin/bash
set -e

# Check if env file exists, if not, create it
if [ ! -f .env ]; then
  echo "Creating .env file with default values..."
  echo "JWT_SECRET_KEY=secure-jwt-key-for-production" > .env
  echo "VAULT_DEV_ROOT_TOKEN_ID=myroot" >> .env
  echo "VAULT_ENABLED=true" >> .env
fi

# Start the services
echo "Starting services with docker-compose..."
docker-compose up -d

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
until curl -s -o /dev/null -w "%{http_code}" http://localhost:8200/v1/sys/health | grep -q "200\|429"; do
  echo "Waiting for Vault to start..."
  sleep 2
done

# Export variables to pass to the container
export VAULT_DEV_ROOT_TOKEN_ID=$(grep VAULT_DEV_ROOT_TOKEN_ID .env | cut -d '=' -f2 || echo "myroot")
echo "Using root token: $VAULT_DEV_ROOT_TOKEN_ID"

# Initialize Vault with secrets using the container
echo "Initializing Vault with secrets..."

# Create a temporary script to run inside the container
cat > /tmp/vault_setup.sh << 'EOF'
#!/bin/sh
set -e

# Set environment variables
export VAULT_TOKEN=$VAULT_DEV_ROOT_TOKEN_ID
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_SKIP_VERIFY=true

# Ensure we're using HTTP not HTTPS
echo "Using Vault address: $VAULT_ADDR"

# Enable KV secrets engine
echo "Enabling KV secrets engine..."
vault secrets enable -version=2 kv

# Create a policy for the API
echo "Creating API policy..."
vault policy write api-policy - << POLICY
path "kv/data/api/*" {
  capabilities = ["read"]
}
POLICY

# Create an AppRole for API
echo "Creating AppRole for API service..."
vault auth enable approle
vault write auth/approle/role/api-role \
  secret_id_ttl=0 \
  token_num_uses=0 \
  token_ttl=24h \
  token_max_ttl=720h \
  secret_id_num_uses=0 \
  policies=api-policy

# Get role-id and secret-id
ROLE_ID=$(vault read -format=json auth/approle/role/api-role/role-id | jq -r .data.role_id)
SECRET_ID=$(vault write -format=json -f auth/approle/role/api-role/secret-id | jq -r .data.secret_id)

echo "Role ID: $ROLE_ID"
echo "Secret ID: $SECRET_ID"

# Store these for the host to use
echo "VAULT_ROLE_ID=$ROLE_ID" > /vault/api_vault_credentials.env
echo "VAULT_SECRET_ID=$SECRET_ID" >> /vault/api_vault_credentials.env

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

# Qdrant config
vault kv put kv/api/qdrant \
  url="${QDRANT_URL:-http://qdrant:6333}" \
  collection_name="${QDRANT_COLLECTION_NAME:-banque_ma_data_catalog}" \
  client_timeout="${QDRANT_CLIENT_TIMEOUT:-120}"

# Ollama config
vault kv put kv/api/ollama \
  host="${OLLAMA_HOST:-http://172.17.0.1:11434}" \
  model_name="${OLLAMA_MODEL_NAME:-llama3:8b}" \
  client_timeout="${OLLAMA_CLIENT_TIMEOUT:-12000}"

# Embedding config
vault kv put kv/api/embedding \
  model_name="${EMBEDDING_MODEL_NAME:-paraphrase-multilingual-MiniLM-L12-v2}"

echo "Vault setup complete inside container!"
EOF

# Copy the script to the container and run it
docker cp /tmp/vault_setup.sh vault:/vault/vault_setup.sh
docker exec -e VAULT_DEV_ROOT_TOKEN_ID=$VAULT_DEV_ROOT_TOKEN_ID vault sh -c "chmod +x /vault/vault_setup.sh && /vault/vault_setup.sh"

# Get the credentials file back from the container
docker cp vault:/vault/api_vault_credentials.env ./api_vault_credentials.env

# Check if we need to load API credentials
if [ -f api_vault_credentials.env ]; then
  echo "Loading API Vault credentials..."
  source api_vault_credentials.env
  
  # Update environment variables for API container
  docker-compose exec -e VAULT_ROLE_ID=$VAULT_ROLE_ID -e VAULT_SECRET_ID=$VAULT_SECRET_ID api sh -c "echo \"Vault credentials loaded: ROLE_ID=${VAULT_ROLE_ID:0:5}... SECRET_ID=${VAULT_SECRET_ID:0:5}...\""
  
  echo "API is now configured to use Vault!"
else
  echo "Error: Failed to generate API Vault credentials."
  exit 1
fi

echo "Setup complete! Your application is now running with Vault integration."
echo "You can access the following services:"
echo "- API: http://localhost:8000"
echo "- Frontend: http://localhost:3000"
echo "- Vault UI: http://localhost:8200/ui"
echo "  (Use token: $VAULT_DEV_ROOT_TOKEN_ID)" 