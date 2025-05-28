#!/bin/bash

echo "=== Testing HTTP to HTTPS Redirection ==="
echo "Sending request to HTTP endpoint (should redirect to HTTPS):"
curl -I -L http://localhost

echo -e "\n\n=== Testing HTTPS Endpoint ==="
echo "Sending request to HTTPS endpoint (should return 200 OK):"
curl -I -L -k https://localhost

echo -e "\n\n=== Testing Security Rules ==="
echo "Testing SQL Injection protection (should be blocked):"
curl -I -L -k "https://localhost/api/data?query=SELECT%20*%20FROM%20users"

echo -e "\n=== Testing XSS protection (should be blocked) ==="
curl -I -L -k "https://localhost/?param=<script>alert(1)</script>"

echo -e "\n=== Testing path traversal protection (should be blocked) ==="
curl -I -L -k "https://localhost/../../etc/passwd" 