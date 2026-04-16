# Rift Scanner Test Vulnerability Lab

A safe, intentionally vulnerable web application for testing the **Rift scanner**. Contains realistic vulnerabilities without allowing RCE, SSRF, or infrastructure compromise.

## Features

### ✓ Vulnerabilities Included

- **Reflected XSS** - User input echoed back without sanitization
- **Stored XSS** - Comments stored in memory and displayed
- **Path Traversal** - Read-only access to mock configuration files
- **SQL Injection** - Vulnerable search endpoint against fake in-memory database
- **IDOR** - Insecure Direct Object Reference on user profiles
- **Default Credentials** - Weak default login (admin/admin123)
- **Sensitive Data Exposure** - API endpoints leak configuration and secrets
- **Broken Authentication** - Weak password verification
- **Security Misconfiguration** - Debug endpoints, exposed robots.txt, sitemap.xml

### ✗ What's NOT Included (Safe)

- ❌ **No RCE** - Cannot execute system commands
- ❌ **No SSRF** - Cannot make requests to internal services
- ❌ **No Real File Access** - All files are mocked in memory
- ❌ **No Database Access** - In-memory fake database only
- ❌ **No Infrastructure Access** - Completely isolated application

## Quick Start

### Option 1: Docker (Recommended)

```bash
cd /Users/mariomejia/vuln-web

# Build and run
docker-compose up -d

# Check if running
docker-compose ps

# View logs
docker-compose logs -f
```

Access at: `http://localhost:5000`

### Option 2: Local Python

```bash
cd /Users/mariomejia/vuln-web

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Access at: `http://localhost:5000`

## Testing the Rift Scanner

### 1. Test Basic Vulnerability Discovery

```bash
# Run httpx to find live hosts
httpx -u http://localhost:5000 -sc -v

# Run nuclei for vulnerabilities
nuclei -u http://localhost:5000 -tags xss,sqli,idor -severity high,critical -v
```

### 2. Specific Vulnerability Tests

#### XSS Detection
```bash
# Reflected XSS
curl "http://localhost:5000/xss/reflected?q=<script>alert('xss')</script>"

# Stored XSS
curl -X POST http://localhost:5000/xss/stored \
  -d "name=test&comment=<img src=x onerror=alert('xss')>"
```

#### Path Traversal Detection
```bash
# Try to access mock files
curl "http://localhost:5000/files?file=config.yaml"
curl "http://localhost:5000/files?file=secrets.env"
curl "http://localhost:5000/files?file=debug.log"
```

#### SQL Injection
```bash
# Normal query
curl "http://localhost:5000/search?q=admin"

# SQL injection payload
curl "http://localhost:5000/search?q=' OR '1'='1"
```

#### IDOR (Insecure Direct Object Reference)
```bash
# Access different users
curl "http://localhost:5000/user/1"
curl "http://localhost:5000/user/2"
curl "http://localhost:5000/user/3"
```

#### Sensitive Data Exposure
```bash
# Debug endpoint
curl "http://localhost:5000/api/debug"

# Config endpoint
curl "http://localhost:5000/api/config"
```

#### Default Credentials
```bash
# Login with default credentials
curl -X POST http://localhost:5000/login \
  -d "username=admin&password=admin123"
```

### 3. Full Rift Scanner Test

```bash
# Run complete scan against the lab
rift-cli scan --url http://localhost:5000 \
  --output /tmp/rift-results.json \
  --modules nuclei_general,xss,traversal,sensitive_files \
  --rate-limit conservative
```

### 4. Expected Findings

When running your scanner, you should detect:

| Vulnerability | Endpoint | Expected Count |
|---------------|----------|-----------------|
| XSS (Reflected) | /xss/reflected?q=payload | 1-3 |
| XSS (Stored) | /xss/stored | 1-2 |
| SQL Injection | /search?q=' OR '1'='1 | 1+ |
| Path Traversal | /files?file=config.yaml | 5 (5 mock files) |
| IDOR | /user/1, /user/2, /user/3 | 3 |
| Sensitive Data | /api/debug, /api/config | 2 |
| Default Creds | /login (admin/admin123) | 1 |
| Information Disclosure | /robots.txt, /sitemap.xml | 2 |

## Available Endpoints

```
GET  /                          - Home page with links
GET  /xss/reflected             - Reflected XSS vulnerability
POST /xss/stored                - Stored XSS (in-memory comments)
GET  /files                     - Path traversal to mock files
GET  /search                    - SQL injection search
GET  /user/<id>                 - IDOR to user profiles
GET  /login                     - Login page
POST /login                     - Login form (admin/admin123)
GET  /dashboard                 - Protected page
GET  /reset?user_id=<id>        - Password reset (weak verification)
GET  /api/debug                 - Debug info (sensitive data)
GET  /api/config                - Config endpoint (sensitive data)
GET  /api/health                - Health check
GET  /sitemap.xml               - Exposed sitemap
GET  /robots.txt                - Exposed robots.txt
```

## Test Credentials

```
Username: admin
Password: admin123

Username: user1
Password: password123

Username: user2
Password: pass456
```

## Mock Files Available

Access via `/files?file=<filename>`

- **config.yaml** - Fake database and API credentials
- **secrets.env** - Environment variables with mock credentials
- **debug.log** - Debug information logs
- **users.json** - User data in JSON format
- **backup.sql** - Database backup with mock data

## Configuration

To modify the vulnerabilities, edit `app.py`:

- Change mock credentials on lines 27-34
- Add/remove mock files in `mock_files` dict (line 40)
- Modify XSS payloads tested on lines 120-125
- Change default login credentials on lines 250-260

## Safety Notes

- ✅ All files are mocked/fake in memory
- ✅ No real database queries executed
- ✅ No system command execution possible
- ✅ No external service calls (mocked only)
- ✅ No persistent storage (data reset on restart)
- ✅ Runs in isolated Docker container
- ✅ Limited to port 5000 only

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove image
docker rmi vuln-web:latest

# Or if using local Python, just stop the process
```

## Integration with Rift Scanner

Use this lab to:

1. **Validate** that nuclei templates are firing correctly
2. **Test** scanner configuration before production scans
3. **Benchmark** scanner performance and accuracy
4. **Train** team on vulnerability types your scanner detects
5. **Regression** test when updating nuclei templates

## Example Rift Scan Command

```bash
# Full vulnerability assessment
nuclei -u http://localhost:5000 \
  -tags cve,sqli,xss,idor,auth,default-login,exposure,disclosure,debug \
  -severity critical,high,medium \
  -c 10 \
  -timeout 10 \
  -rate-limit 50 \
  -json \
  -o /tmp/rift-vuln-lab-results.json

# Parse results
cat /tmp/rift-vuln-lab-results.json | jq '.[] | {template: .template_id, severity: .info.severity, type: .type}'
```

## Support

If you encounter issues:

1. Check that port 5000 is not in use: `lsof -i :5000`
2. Verify Docker is running: `docker ps`
3. Check logs: `docker-compose logs -f`
4. Restart: `docker-compose restart`

---

**Last Updated:** 2024-01-15
**Version:** 1.0
**Status:** Production-ready for testing
