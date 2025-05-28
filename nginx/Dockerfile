FROM owasp/modsecurity-crs:nginx-alpine

# Switch to root for file operations
USER root

# Create necessary directories
RUN mkdir -p /usr/share/nginx/html/errors \
    && mkdir -p /etc/modsecurity

# Copy our custom nginx.conf file
COPY nginx.conf /etc/nginx/nginx.conf

# Copy SSL certificates
COPY ssl/ /etc/nginx/ssl/

# Copy custom error page for ModSecurity blocks
COPY error_pages/403_modsecurity.html /usr/share/nginx/html/errors/

# Basic ModSecurity configuration
COPY modsecurity/* /etc/modsecurity/

# Create a symlink to include our custom rules
RUN ln -sf /etc/modsecurity/custom-rules.conf /etc/modsecurity.d/custom-rules.conf

# Set proper permissions
RUN chmod -R 755 /usr/share/nginx/html/errors \
    && chmod -R 755 /etc/nginx/ssl \
    && chmod -R 755 /etc/modsecurity

# Expose ports
EXPOSE 80 443

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 