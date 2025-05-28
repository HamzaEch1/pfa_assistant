#!/bin/bash

# Generate a private key
openssl genrsa -out nginx.key 2048

# Generate a CSR (Certificate Signing Request)
openssl req -new -key nginx.key -out nginx.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate a self-signed certificate
openssl x509 -req -days 365 -in nginx.csr -signkey nginx.key -out nginx.crt

# Set appropriate permissions
chmod 600 nginx.key
chmod 644 nginx.crt

# Clean up
rm nginx.csr

echo "Self-signed SSL certificate generated successfully!"
echo "Files created:"
echo "- nginx.key (private key)"
echo "- nginx.crt (certificate)" 