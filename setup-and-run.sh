#!/bin/bash

echo "=== Setting up HTTPS-only secure Docker environment ==="

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p nginx/ssl
mkdir -p nginx/modsecurity
mkdir -p nginx/error_pages

# Check if SSL certificates exist
if [ ! -f nginx/ssl/nginx.key ] || [ ! -f nginx/ssl/nginx.crt ]; then
    echo "SSL certificates not found. Generating self-signed certificates..."
    
    # Generate SSL certificates
    cd nginx/ssl
    
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
    rm -f nginx.csr
    
    cd ../../
    
    echo "SSL certificates generated successfully!"
fi

# Create ModSecurity configuration if it doesn't exist
if [ ! -f nginx/modsecurity/modsecurity.conf ]; then
    echo "Creating ModSecurity configuration..."
    cat > nginx/modsecurity/modsecurity.conf << 'EOF'
# ModSecurity configuration
SecRuleEngine On
SecRequestBodyAccess On
SecRequestBodyLimit 13107200
SecRequestBodyNoFilesLimit 131072
SecRequestBodyInMemoryLimit 131072
SecResponseBodyAccess On
SecResponseBodyMimeType text/plain text/html text/xml application/json
SecResponseBodyLimit 524288
SecTmpDir /tmp/
SecDataDir /tmp/
SecUploadDir /tmp/
SecDebugLog /var/log/nginx/modsec_debug.log
SecDebugLogLevel 3
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABIJDEFHZ
SecAuditLogType Serial
SecAuditLog /var/log/nginx/modsec_audit.log
SecArgumentSeparator &
SecCookieFormat 0
SecStatusEngine On
SecDefaultAction "phase:1,log,auditlog,deny,status:403,redirect:/errors/403_modsecurity.html"
EOF
fi

# Make sure error pages directory exists
if [ ! -f nginx/error_pages/403_modsecurity.html ]; then
    echo "Creating default error page..."
    cat > nginx/error_pages/403_modsecurity.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Security Alert - Access Denied</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f8f8f8;
            padding: 50px;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #e74c3c;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .button {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Security Alert - Access Denied</h1>
        <p>Our security system has detected potentially malicious activity in your request. 
        The request has been blocked to protect our systems and users.</p>
        <p>If you believe this is a mistake, please contact the system administrator.</p>
        <a href="/" class="button">Return to Home</a>
    </div>
</body>
</html>
EOF
fi

# Set proper permissions for Docker
echo "Setting proper permissions..."
chmod -R 755 nginx

# Start Docker containers
echo "Starting Docker containers..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "=== Setup complete! ==="
echo "Your secure HTTPS-only environment is now running."
echo "- Nginx is running with HTTPS enforced"
echo "- All HTTP traffic is automatically redirected to HTTPS"
echo "- ModSecurity is enabled for additional security"
echo ""
echo "You can access your application at: https://localhost"
echo "To test security, run: ./test-https-enforcement.sh" 