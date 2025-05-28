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

# Initialize Vault with secrets
echo "Initializing Vault with secrets..."
export VAULT_ADDR=http://localhost:8200
export VAULT_DEV_ROOT_TOKEN_ID=$(grep VAULT_DEV_ROOT_TOKEN_ID .env | cut -d '=' -f2)

# Run the setup script
./vault/setup_vault.sh

# Check if we need to load API credentials
if [ -f api_vault_credentials.env ]; then
  echo "Loading API Vault credentials..."
  source api_vault_credentials.env
  
  # Update environment variables for API container
  docker-compose exec api sh -c "export VAULT_ROLE_ID=$VAULT_ROLE_ID && export VAULT_SECRET_ID=$VAULT_SECRET_ID"
  
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