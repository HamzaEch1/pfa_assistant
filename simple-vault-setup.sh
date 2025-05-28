#!/bin/bash
set -e

# Set the root token (should match the one in the docker-compose.yml)
ROOT_TOKEN="myroot"

echo "Setting up Vault with root token: $ROOT_TOKEN"

# Make sure Vault is running
if ! docker ps | grep -q vault; then
  echo "Starting all services..."
  docker-compose up -d
fi

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
until curl -s -o /dev/null -w "%{http_code}" http://localhost:8200/v1/sys/health | grep -q "200\|429"; do
  echo "Waiting for Vault to start..."
  sleep 2
done

# Install jq in the Vault container
echo "Installing jq in the Vault container..."
docker exec vault sh -c "apk add --no-cache jq"

# Run commands inside the vault container
echo "Configuring Vault..."
docker exec -e VAULT_TOKEN=$ROOT_TOKEN -e VAULT_ADDR=http://127.0.0.1:8200 vault sh -c '
  # Enable KV secrets engine
  vault secrets enable -version=2 kv
  
  # Create a policy for the API
  vault policy write api-policy - << EOF
path "kv/data/api/*" {
  capabilities = ["read"]
}
EOF
  
  # Create an AppRole for API authentication
  vault auth enable approle
  vault write auth/approle/role/api-role \
    secret_id_ttl=0 \
    token_num_uses=0 \
    token_ttl=24h \
    token_max_ttl=720h \
    secret_id_num_uses=0 \
    policies=api-policy
  
  # Get role-id and secret-id
  echo "Retrieving API credentials..."
  ROLE_ID=$(vault read -format=json auth/approle/role/api-role/role-id | jq -r .data.role_id)
  SECRET_ID=$(vault write -format=json -f auth/approle/role/api-role/secret-id | jq -r .data.secret_id)
  
  echo "VAULT_ROLE_ID=$ROLE_ID" > /tmp/api_vault_credentials.env
  echo "VAULT_SECRET_ID=$SECRET_ID" >> /tmp/api_vault_credentials.env
  
  # Store secrets in Vault
  echo "Storing secrets in Vault..."
  
  # Database credentials
  vault kv put kv/api/db \
    host="db" \
    port="5432" \
    user="user" \
    password="password" \
    dbname="mydb"
  
  # JWT secret
  vault kv put kv/api/jwt \
    secret_key="secure-jwt-key-for-production" \
    algorithm="HS256" \
    exp_delta_seconds="3600"
  
  # Qdrant configuration
  vault kv put kv/api/qdrant \
    url="http://qdrant:6333" \
    collection_name="banque_ma_data_catalog" \
    client_timeout="120"
  
  # Ollama configuration
  vault kv put kv/api/ollama \
    host="http://172.17.0.1:11434" \
    model_name="llama3:8b" \
    client_timeout="12000"
  
  # Embedding model configuration
  vault kv put kv/api/embedding \
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
  
  echo "Vault setup complete!"
'

# Get credentials file from container
docker exec vault cat /tmp/api_vault_credentials.env > api_vault_credentials.env
echo "Vault credentials saved to api_vault_credentials.env"

# Read credentials
if [ -f api_vault_credentials.env ]; then
  source api_vault_credentials.env
  
  if [ -n "$VAULT_ROLE_ID" ] && [ -n "$VAULT_SECRET_ID" ]; then
    echo "API credentials:"
    echo "VAULT_ROLE_ID=${VAULT_ROLE_ID:0:5}..."
    echo "VAULT_SECRET_ID=${VAULT_SECRET_ID:0:5}..."

    # Update API container with credentials
    docker-compose exec -e VAULT_ROLE_ID=$VAULT_ROLE_ID -e VAULT_SECRET_ID=$VAULT_SECRET_ID -e VAULT_ENABLED=true api sh -c "
      echo 'export VAULT_ROLE_ID=$VAULT_ROLE_ID' >> /etc/environment && 
      echo 'export VAULT_SECRET_ID=$VAULT_SECRET_ID' >> /etc/environment && 
      echo 'export VAULT_ENABLED=true' >> /etc/environment &&
      echo 'Vault credentials configured for API service'
    "
    
    echo "API container updated with Vault credentials"
    
    # Restart the API service to apply the changes
    echo "Restarting API service to apply Vault configuration..."
    docker-compose restart api
  else
    echo "Error: Missing or empty credentials"
    exit 1
  fi
else
  echo "Error: Failed to generate API Vault credentials."
  exit 1
fi

echo "Setup complete! Your application is now running with Vault integration."
echo "You can access the following services:"
echo "- API: http://localhost:8000"
echo "- Frontend: http://localhost:3000"
echo "- Vault UI: http://localhost:8200/ui"
echo "  (Use token: $ROOT_TOKEN)" 