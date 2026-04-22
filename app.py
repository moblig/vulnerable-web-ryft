"""
Rift Scanner Test Vulnerable Web Application
==============================================

INTENTIONALLY VULNERABLE for testing Rift scanner.
Safe vulnerabilities only - no RCE, SSRF, or infrastructure access.

Vulnerabilities included:
- Reflected XSS
- Stored XSS (in-memory only)
- Path Traversal (read-only, fake files)
- SQL Injection (against fake in-memory DB)
- Sensitive Data Exposure (mock credentials)
- Broken Authentication (weak default creds)
- IDOR (Insecure Direct Object Reference)
- Security Misconfiguration (debug endpoints)
- Default Credentials
"""

from flask import Flask, request, render_template_string, jsonify
import os
from urllib.parse import unquote
import json

app = Flask(__name__)
app.secret_key = 'vulnerable-test-key'

# In-memory data stores (reset on app restart)
users_db = {
    '1': {'id': '1', 'username': 'admin', 'email': 'admin@test.com', 'password': 'admin123'},
    '2': {'id': '2', 'username': 'user1', 'email': 'user1@test.com', 'password': 'password123'},
    '3': {'id': '3', 'username': 'user2', 'email': 'user2@test.com', 'password': 'pass456'},
}

comments_store = []  # For stored XSS testing

# Mock files for path traversal (all fake, no real files)
mock_files = {
    'config.yaml': """
# Mock Configuration File
database:
  host: mock-db-server
  port: 5432
  username: mock_user
  password: MockPassword123!
  name: test_database

api:
  key: MOCK_API_KEY_abc123xyz789
  secret: MOCK_SECRET_key_def456

email:
  from: noreply@mock-company.com
  password: MockEmailPass789!
""",
    'secrets.env': """
DATABASE_URL=postgresql://mock_user:MockPassword123!@mock-db.example.com:5432/testdb
API_KEY=MOCK_API_KEY_abc123xyz789
API_SECRET=MOCK_SECRET_key_def456
AWS_ACCESS_KEY_ID=AKIA1234567890ABCD12
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
STRIPE_API_KEY=sk_live_51234567890abcdefghijklmnopqrstuvwxyz
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
SLACK_BOT_TOKEN=xoxb-123456789012-123456789012-abcdefghijklmnopqrstuvwxyz12
SLACK_WEBHOOK=https://hooks.slack.com/services/T123456789/B123456789/1234567890abcdefghijklmnop
SENDGRID_API_KEY=SG.1234567890abcdefghijklmnopqrstuvwxyz
MAILGUN_API_KEY=key-1234567890abcdefghijklmnopqrstuvwxyz
JWT_SECRET=your-secret-key-here-12345
PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7W8zUhPeKfQRc\\nH6x7VsZbXwrXE7VL0HhEF7h0JZ2K1234567890abcdefghijklmnopqrstuvwxyzAB\\n-----END PRIVATE KEY-----
""",
    'debug.log': """
[2024-01-15 10:23:45] User login attempt: admin@test.com
[2024-01-15 10:24:12] Password validation passed
[2024-01-15 10:24:13] Session created: sess_abc123xyz789
[2024-01-15 10:25:01] Database query: SELECT * FROM users WHERE id=1
[2024-01-15 10:25:02] API call to external service: mock-api.example.com
[2024-01-15 10:26:45] User admin updated profile
""",
    'users.json': """
[
  {"id": 1, "username": "admin", "email": "admin@test.com", "role": "admin", "api_key": "mock_key_123"},
  {"id": 2, "username": "user1", "email": "user1@test.com", "role": "user", "api_key": "mock_key_456"},
  {"id": 3, "username": "user2", "email": "user2@test.com", "role": "user", "api_key": "mock_key_789"}
]
""",
    'backup.sql': """
-- Mock database backup
INSERT INTO users VALUES (1, 'admin', 'admin@test.com', 'mock_hash_123');
INSERT INTO users VALUES (2, 'user1', 'user1@test.com', 'mock_hash_456');
INSERT INTO credentials VALUES ('aws', 'AKIAIOSFODNN7EXAMPLE', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY');
INSERT INTO credentials VALUES ('stripe', 'sk_test_4eC39HqLyjWDarhu1234567890', '');
""",
}

# ==================== ROUTES ====================

@app.route('/', methods=['GET'])
def index():
    """Home page - safe"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rift Scanner Test Vulnerability Lab</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .section { background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #dc3545; }
            .title { color: #dc3545; font-weight: bold; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
            code { background: #eee; padding: 2px 5px; }
        </style>
    </head>
    <body>
        <h1>🔓 Rift Scanner - Vulnerability Test Lab</h1>
        <p>This application contains intentional vulnerabilities for testing the Rift scanner.</p>

        <div class="section">
            <div class="title">✓ XSS (Cross-Site Scripting)</div>
            <p>
                <a href="/xss/reflected">Reflected XSS</a> - User input echoed back<br>
                <a href="/xss/stored">Stored XSS</a> - Comments stored in memory<br>
                Test: <code>&lt;script&gt;alert('xss')&lt;/script&gt;</code>
            </p>
        </div>

        <div class="section">
            <div class="title">✓ Path Traversal (Read-Only)</div>
            <p>
                <a href="/files?file=config.yaml">View Config</a><br>
                <a href="/files?file=secrets.env">View Secrets</a><br>
                <a href="/files?file=debug.log">View Debug Log</a><br>
                Available files: config.yaml, secrets.env, debug.log, users.json, backup.sql
            </p>
        </div>

        <div class="section">
            <div class="title">✓ SQL Injection (Mock)</div>
            <p>
                <a href="/search">Search Users</a> - Vulnerable to SQLi<br>
                Test: <code>' OR '1'='1</code>
            </p>
        </div>

        <div class="section">
            <div class="title">✓ IDOR (Insecure Direct Object Reference)</div>
            <p>
                <a href="/user/1">View User 1</a><br>
                <a href="/user/2">View User 2</a><br>
                <a href="/user/3">View User 3</a><br>
                Escalate privileges by modifying user IDs
            </p>
        </div>

        <div class="section">
            <div class="title">✓ Default Credentials</div>
            <p>
                <a href="/login">Login Page</a><br>
                Credentials: <code>admin / admin123</code> or <code>user1 / password123</code>
            </p>
        </div>

        <div class="section">
            <div class="title">✓ Sensitive Data Exposure</div>
            <p>
                <a href="/api/debug">Debug Info Endpoint</a> - Exposes system info<br>
                <a href="/api/config">Config Endpoint</a> - Leaks configuration
            </p>
        </div>

        <div class="section">
            <div class="title">✓ Broken Authentication</div>
            <p>
                <a href="/dashboard">Dashboard (login required)</a><br>
                Password reset without verification: <code>/reset?user_id=1</code>
            </p>
        </div>
    </body>
    </html>
    """
    return html


@app.route('/xss/reflected', methods=['GET'])
def xss_reflected():
    """Reflected XSS vulnerability"""
    search = request.args.get('q', '')
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Search</title></head>
    <body>
        <h2>Search Results</h2>
        <form method="GET">
            <input type="text" name="q" placeholder="Search...">
            <button>Search</button>
        </form>
        <p>You searched for: <b>{search}</b></p>
    </body>
    </html>
    """
    return html


@app.route('/xss/stored', methods=['GET', 'POST'])
def xss_stored():
    """Stored XSS vulnerability - comments stored in memory"""
    if request.method == 'POST':
        name = request.form.get('name', '')
        comment = request.form.get('comment', '')
        if name and comment:
            comments_store.append({'name': name, 'comment': comment})
        return """
        <script>
            alert('Comment posted!');
            window.location = '/xss/stored';
        </script>
        """

    comments_html = ""
    for c in comments_store:
        comments_html += f"<div style='border: 1px solid #ccc; padding: 10px; margin: 10px 0;'><b>{c['name']}</b>: {c['comment']}</div>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Comments</title></head>
    <body>
        <h2>Comments</h2>
        <form method="POST">
            <input type="text" name="name" placeholder="Your name" required>
            <textarea name="comment" placeholder="Your comment"></textarea>
            <button>Post Comment</button>
        </form>
        <h3>Previous Comments:</h3>
        {comments_html if comments_html else '<p>No comments yet</p>'}
    </body>
    </html>
    """
    return html


@app.route('/files', methods=['GET'])
def path_traversal():
    """Path Traversal - Read-only fake files"""
    filename = request.args.get('file', '')

    # Security: Only allow reading from mock files
    # No access to real filesystem
    if filename not in mock_files:
        return "File not found. Available files: " + ", ".join(mock_files.keys()), 404

    content = mock_files[filename]
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>File Viewer</title></head>
    <body>
        <h2>File: {filename}</h2>
        <a href="/files">Back</a>
        <pre style="background: #f5f5f5; padding: 10px; border: 1px solid #ccc;">{content}</pre>
    </body>
    </html>
    """
    return html


@app.route('/search', methods=['GET'])
def search_sql_injection():
    """SQL Injection - vulnerable to SQLi (against fake DB)"""
    query = request.args.get('q', '')

    # INTENTIONALLY VULNERABLE - simulate SQL injection
    # This is not a real SQL query, just demonstrates the vulnerability
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>User Search</title></head>
    <body>
        <h2>Search Users</h2>
        <form method="GET">
            <input type="text" name="q" placeholder="Search username...">
            <button>Search</button>
        </form>
        <h3>Results:</h3>
        <p>Query: SELECT * FROM users WHERE username LIKE '%{query}%'</p>
    """

    # Simulate SQL injection results
    if query:
        if "' OR '1'='1" in query or "' OR 1=1" in query:
            html += "<p><b>SQL Injection detected!</b> Returning all users:</p><ul>"
            for uid, user in users_db.items():
                html += f"<li>{user['username']} ({user['email']})</li>"
            html += "</ul>"
        else:
            # Normal search
            results = [u for u in users_db.values() if query.lower() in u['username'].lower()]
            if results:
                html += "<ul>"
                for user in results:
                    html += f"<li>{user['username']} ({user['email']})</li>"
                html += "</ul>"
            else:
                html += "<p>No results found</p>"

    html += "</body></html>"
    return html


@app.route('/user/<user_id>', methods=['GET'])
def idor_vulnerability(user_id):
    """IDOR - Access any user by ID"""
    if user_id not in users_db:
        return "User not found", 404

    user = users_db[user_id]
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>User Profile</title></head>
    <body>
        <h2>User Profile</h2>
        <p><b>ID:</b> {user['id']}</p>
        <p><b>Username:</b> {user['username']}</p>
        <p><b>Email:</b> {user['email']}</p>
        <p><b>Password Hash:</b> {user['password']}</p>
        <a href="/user/1">User 1</a> | <a href="/user/2">User 2</a> | <a href="/user/3">User 3</a>
    </body>
    </html>
    """
    return html


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Weak authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # INTENTIONALLY VULNERABLE - weak auth check
        for user in users_db.values():
            if user['username'] == username and user['password'] == password:
                return f"""
                <html>
                <body>
                    <h2>Login Successful!</h2>
                    <p>Welcome, {username}!</p>
                    <p>Session ID: sess_{user['id']}_abc123xyz</p>
                    <a href="/dashboard">Go to Dashboard</a>
                </body>
                </html>
                """

        return """
        <html>
        <body>
            <h2>Login Failed</h2>
            <p>Invalid credentials. Try admin/admin123</p>
            <a href="/login">Back to Login</a>
        </body>
        </html>
        """

    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Login</title></head>
    <body>
        <h2>Login</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button>Login</button>
        </form>
        <p>Test credentials: admin / admin123</p>
    </body>
    </html>
    """
    return html


@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Protected page - but has weak auth"""
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard</title></head>
    <body>
        <h2>Dashboard</h2>
        <p>Sensitive user data would be displayed here.</p>
        <p><a href="/user/1">View Admin User</a></p>
    </body>
    </html>
    """
    return html


@app.route('/reset', methods=['GET'])
def reset_password():
    """Password reset without verification - IDOR + weak auth"""
    user_id = request.args.get('user_id', '')
    if user_id in users_db:
        user = users_db[user_id]
        return f"""
        <html>
        <body>
            <h2>Password Reset</h2>
            <p>Password reset link sent to {user['email']}</p>
            <p>Reset token: token_abc123xyz_for_user_{user_id}</p>
        </body>
        </html>
        """
    return "User not found", 404


@app.route('/api/debug', methods=['GET'])
def api_debug():
    """Debug endpoint - exposes sensitive info"""
    return jsonify({
        'status': 'debug_mode_enabled',
        'environment': 'test',
        'database_host': 'mock-db.example.com',
        'database_port': 5432,
        'credentials': {
            'github_token': 'ghp_1234567890abcdefghijklmnopqrstuvwxyz',
            'slack_token': 'xoxb-123456789012-123456789012-abcdefghijklmnopqrstuvwxyz12',
            'aws_access_key_id': 'AKIA1234567890ABCD12',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'stripe_api_key': 'sk_live_51234567890abcdefghijklmnopqrstuvwxyz',
            'sendgrid_api_key': 'SG.1234567890abcdefghijklmnopqrstuvwxyz'
        },
        'api_key': 'MOCK_API_KEY_abc123xyz789',
        'api_secret': 'MOCK_SECRET_key_def456',
        'debug_info': {
            'app_version': '1.0.0-debug',
            'python_version': '3.9',
            'flask_debug': True,
            'secret_key': app.secret_key
        }
    })


@app.route('/api/config', methods=['GET'])
def api_config():
    """Config endpoint - leaks configuration"""
    return jsonify({
        'config': {
            'database': {
                'host': 'mock-db.example.com',
                'port': 5432,
                'username': 'mock_user',
                'password': 'MockPassword123!',
                'url': 'postgresql://mock_user:MockPassword123!@mock-db.example.com:5432/testdb'
            },
            'api': {
                'github_token': 'ghp_1234567890abcdefghijklmnopqrstuvwxyz',
                'github_oauth': 'ghu_1234567890abcdefghijklmnopqrstuvwxyzAB',
                'slack_token': 'xoxb-123456789012-123456789012-abcdefghijklmnopqrstuvwxyz12',
                'slack_webhook': 'https://hooks.slack.com/services/T123456789/B123456789/1234567890abcdefghijklmnop',
                'key': 'MOCK_API_KEY_abc123xyz789',
                'secret': 'MOCK_SECRET_key_def456',
                'endpoint': 'https://api.example.com'
            },
            'cloud': {
                'aws_access_key_id': 'AKIA1234567890ABCD12',
                'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                'aws_region': 'us-east-1'
            },
            'payment': {
                'stripe_public_key': 'pk_live_51234567890abcdefghijklmnopqrstuvwxyz',
                'stripe_secret_key': 'sk_live_51234567890abcdefghijklmnopqrstuvwxyz',
                'stripe_webhook_secret': 'whsec_1234567890abcdefghijklmnopqrstuvwxyz'
            },
            'email': {
                'sendgrid_api_key': 'SG.1234567890abcdefghijklmnopqrstuvwxyz',
                'mailgun_api_key': 'key-1234567890abcdefghijklmnopqrstuvwxyz'
            },
            'auth': {
                'jwt_secret': 'your-secret-key-here-12345',
                'jwt_algorithm': 'HS256',
                'private_key': '-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7W8zUhPeKfQRc\\nH6x7VsZbXwrXE7VL0HhEF7h0JZ2K1234567890abcdefghijklmnopqrstuvwxyzAB\\n-----END PRIVATE KEY-----',
                'session_timeout': 3600
            }
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'rift-test-lab'})


@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    """Exposed sitemap - information disclosure"""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>/</loc><priority>1.0</priority></url>
    <url><loc>/xss/reflected</loc><priority>0.8</priority></url>
    <url><loc>/xss/stored</loc><priority>0.8</priority></url>
    <url><loc>/files</loc><priority>0.8</priority></url>
    <url><loc>/search</loc><priority>0.8</priority></url>
    <url><loc>/user/1</loc><priority>0.7</priority></url>
    <url><loc>/user/2</loc><priority>0.7</priority></url>
    <url><loc>/user/3</loc><priority>0.7</priority></url>
    <url><loc>/login</loc><priority>0.9</priority></url>
    <url><loc>/api/debug</loc><priority>0.6</priority></url>
    <url><loc>/api/config</loc><priority>0.6</priority></url>
</urlset>
"""
    return xml, 200, {'Content-Type': 'application/xml'}


@app.route('/robots.txt', methods=['GET'])
def robots():
    """Exposed robots.txt - information disclosure"""
    txt = """User-agent: *
Disallow: /admin
Disallow: /api/debug
Disallow: /api/config
Disallow: /dashboard
Allow: /

# Sensitive paths that should be hidden
/admin/
/api/secrets
/backup/
/config/
"""
    return txt, 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
