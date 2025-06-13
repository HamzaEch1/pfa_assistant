#!/usr/bin/env python3
"""
Simple test web server for ModSecurity testing
This server will be placed behind ModSecurity to test protection capabilities
"""

from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

# Simple HTML template for testing
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ModSecurity Test Target</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .test-form { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .result { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 3px; }
        .error { background: #ffe8e8; }
        input[type="text"], textarea { width: 100%; padding: 8px; margin: 5px 0; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 ModSecurity Test Target</h1>
        <p>This is a test application to verify ModSecurity protection.</p>
        
        <div class="test-form">
            <h3>SQL Injection Test</h3>
            <form method="GET">
                <input type="text" name="id" placeholder="Enter user ID (try: ' OR '1'='1)" value="{{ request.args.get('id', '') }}">
                <button type="submit">Test SQL</button>
            </form>
            {% if request.args.get('id') %}
            <div class="result">
                <strong>SQL Query Result:</strong> SELECT * FROM users WHERE id = '{{ request.args.get('id') }}'
                <br><em>If you see this, ModSecurity didn't block the request!</em>
            </div>
            {% endif %}
        </div>

        <div class="test-form">
            <h3>XSS Test</h3>
            <form method="GET">
                <input type="text" name="q" placeholder="Enter search query (try: <script>alert('XSS')</script>)" value="{{ request.args.get('q', '') }}">
                <button type="submit">Test XSS</button>
            </form>
            {% if request.args.get('q') %}
            <div class="result">
                <strong>Search Result:</strong> {{ request.args.get('q') | safe }}
                <br><em>If you see this, ModSecurity didn't block the request!</em>
            </div>
            {% endif %}
        </div>

        <div class="test-form">
            <h3>File Inclusion Test</h3>
            <form method="GET">
                <input type="text" name="file" placeholder="Enter file path (try: ../../../etc/passwd)" value="{{ request.args.get('file', '') }}">
                <button type="submit">Test LFI</button>
            </form>
            {% if request.args.get('file') %}
            <div class="result">
                <strong>File Access Attempt:</strong> {{ request.args.get('file') }}
                <br><em>If you see this, ModSecurity didn't block the request!</em>
            </div>
            {% endif %}
        </div>

        <div class="test-form">
            <h3>Command Injection Test</h3>
            <form method="POST">
                <input type="text" name="cmd" placeholder="Enter command (try: ; ls -la)" value="{{ request.form.get('cmd', '') }}">
                <button type="submit">Test CMD</button>
            </form>
            {% if request.form.get('cmd') %}
            <div class="result">
                <strong>Command Attempt:</strong> {{ request.form.get('cmd') }}
                <br><em>If you see this, ModSecurity didn't block the request!</em>
            </div>
            {% endif %}
        </div>

        <h3>Request Information</h3>
        <div class="result">
            <strong>Method:</strong> {{ request.method }}<br>
            <strong>URL:</strong> {{ request.url }}<br>
            <strong>User-Agent:</strong> {{ request.headers.get('User-Agent', 'Not provided') }}<br>
            <strong>Remote Address:</strong> {{ request.remote_addr }}<br>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page with test forms"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/test', methods=['GET', 'POST'])
def api_test():
    """API endpoint for automated testing"""
    data = {
        'method': request.method,
        'args': dict(request.args),
        'form': dict(request.form),
        'headers': dict(request.headers),
        'json': request.get_json() if request.is_json else None,
        'status': 'success',
        'message': 'Request processed successfully - ModSecurity did not block this request'
    }
    return jsonify(data)

@app.route('/vulnerable/<path:filename>')
def vulnerable_file_access(filename):
    """Vulnerable endpoint for file inclusion testing"""
    return jsonify({
        'file_requested': filename,
        'message': 'File access attempt - if you see this, ModSecurity failed to block LFI',
        'status': 'vulnerable'
    })

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint for SQL injection testing"""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # Simulate vulnerable SQL query
    fake_query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    
    return jsonify({
        'query': fake_query,
        'username': username,
        'message': 'Login attempt processed - if you see this, ModSecurity failed to block SQL injection',
        'status': 'vulnerable'
    })

@app.route('/search')
def search():
    """Search endpoint for XSS testing"""
    query = request.args.get('q', '')
    return f"""
    <html>
    <body>
        <h1>Search Results</h1>
        <p>You searched for: {query}</p>
        <p><em>If you see this page with unescaped content, ModSecurity failed to block XSS</em></p>
    </body>
    </html>
    """

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors (likely from ModSecurity)"""
    return jsonify({
        'error': 'Forbidden',
        'message': 'This request was blocked, likely by ModSecurity',
        'status_code': 403
    }), 403

if __name__ == '__main__':
    print("🎯 Starting ModSecurity Test Target Server")
    print("📡 Server will run on http://localhost:5000")
    print("🔒 Place this behind ModSecurity/Nginx for testing")
    print("=" * 50)
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=True) 