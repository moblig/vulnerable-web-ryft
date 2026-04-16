# Rift Scanner Integration Guide

How to use the Rift Vulnerability Test Lab to validate your scanner configuration.

## Quick Start (5 minutes)

```bash
# 1. Start the vulnerable app
cd /Users/mariomejia/vuln-web
docker-compose up -d

# 2. Run test suite
bash test-vulnerabilities.sh

# 3. Run nuclei against it
nuclei -u http://localhost:5000 -tags xss,sqli,idor -v

# 4. View results
cat /tmp/rift-vuln-test-results.txt
```

## Step-by-Step Integration

### Step 1: Start the Test Lab

```bash
# Using Docker (recommended)
cd /Users/mariomejia/vuln-web
docker-compose up -d

# Or local Python
python app.py  # Runs on http://localhost:5000
```

Verify it's running:
```bash
curl http://localhost:5000 | head -5
```

### Step 2: Run Your Scanner Against It

#### Option A: Using Nuclei Directly

```bash
# Scan for XSS vulnerabilities
nuclei -u http://localhost:5000 -tags xss -v

# Scan for SQL injection
nuclei -u http://localhost:5000 -tags sqli -v

# Scan for IDOR
nuclei -u http://localhost:5000 -tags idor -v

# Comprehensive scan (all vulnerability types)
nuclei -u http://localhost:5000 \
  -tags cve,sqli,xss,idor,auth,default-login,exposure,disclosure \
  -severity critical,high,medium \
  -timeout 10 \
  -json \
  -o /tmp/nuclei-results.json
```

#### Option B: Using httpx + Nuclei (Rift Flow)

```bash
# Step 1: Discover live hosts
httpx -u http://localhost:5000 -sc -v -o /tmp/live-hosts.txt

# Step 2: Run nuclei on discovered hosts
nuclei -l /tmp/live-hosts.txt \
  -tags xss,sqli,idor,auth,default-login \
  -severity high,critical \
  -json \
  -o /tmp/nuclei-findings.json
```

#### Option C: Using FFUF + Nuclei

```bash
# Step 1: Discover directories
ffuf -u http://localhost:5000/FUZZ -w common.txt -mc 200,204,405

# Step 2: Run nuclei on discovered paths
nuclei -u http://localhost:5000 \
  -tags xss,sqli,idor,traversal,exposure \
  -json \
  -o /tmp/nuclei-findings.json
```

### Step 3: Validate Template Coverage

Check which vulnerabilities your scanner detects:

```bash
# Run comprehensive scan
nuclei -u http://localhost:5000 \
  -tags cve,sqli,xss,xxe,ssti,injection,idor,auth,default-login,cors,headers,exposure,disclosure,debug \
  -severity critical,high \
  -json \
  -o /tmp/results.json

# Show detected vulnerabilities
jq '.[] | {name: .info.name, severity: .info.severity, template: .template_id}' /tmp/results.json

# Count by severity
jq 'group_by(.info.severity) | map({severity: .[0].info.severity, count: length})' /tmp/results.json
```

### Step 4: Expected Findings

When running your scanner against this lab, you should detect approximately:

```
✅ 1-3     Reflected XSS findings
✅ 1-2     Stored XSS findings
✅ 3-5     Path Traversal findings (5 mock files)
✅ 2-3     SQL Injection findings
✅ 3       IDOR findings (3 users)
✅ 2       Sensitive Data Exposure findings
✅ 1-2     Default Credentials findings
✅ 2       Information Disclosure findings (robots.txt, sitemap.xml)
---
   ~18-21  Total vulnerabilities detected

```

### Step 5: Analyze Results

```bash
# Pretty print results
jq '.' /tmp/nuclei-results.json | less

# Extract unique templates that fired
jq -r '.[] | .template_id' /tmp/nuclei-results.json | sort | uniq

# Count findings by severity
jq '.[] | .info.severity' /tmp/nuclei-results.json | sort | uniq -c

# Export to CSV for analysis
jq -r '.[] | [.template_id, .info.name, .info.severity, .type] | @csv' /tmp/nuclei-results.json > /tmp/findings.csv
```

## Validating Specific Modules

### Validate XSS Detection

```bash
# Test reflected XSS detection
nuclei -u "http://localhost:5000/xss/reflected?q=<script>alert('xss')</script>" \
  -tags xss \
  -v

# Test stored XSS detection
nuclei -u http://localhost:5000/xss/stored -tags xss -v
```

**Expected:** 1-3 XSS vulnerabilities detected

### Validate Path Traversal Detection

```bash
# Test path traversal module
nuclei -u "http://localhost:5000/files?file=config.yaml" \
  -tags path-traversal,traversal,lfi \
  -v
```

**Expected:** 1+ Path Traversal findings

### Validate SQL Injection Detection

```bash
# Test SQLi module
nuclei -u "http://localhost:5000/search?q=' OR '1'='1" \
  -tags sqli,injection \
  -v
```

**Expected:** 1+ SQL Injection findings

### Validate IDOR Detection

```bash
# Test IDOR module
nuclei -u http://localhost:5000/user/1 \
  -tags idor \
  -v
```

**Expected:** 1+ IDOR findings

### Validate Authentication Issues

```bash
# Test auth detection
nuclei -u http://localhost:5000/login \
  -tags auth,default-login,unauth \
  -v
```

**Expected:** 1+ Authentication findings

### Validate Information Disclosure

```bash
# Test disclosure detection
nuclei -u http://localhost:5000 \
  -tags disclosure,exposure,debug,logs \
  -v
```

**Expected:** 2+ Information Disclosure findings

## Integration with Your Rift Scanner

### Option 1: Add to Your Test Suite

Create a test in your CI/CD pipeline:

```bash
#!/bin/bash
# test-rift-vulnerabilities.sh

# Start test lab
docker-compose -f /Users/mariomejia/vuln-web/docker-compose.yml up -d
sleep 5

# Run scanner
nuclei -u http://localhost:5000 \
  -tags cve,sqli,xss,idor,auth \
  -severity high,critical \
  -json \
  -o test-results.json

# Check results
FINDINGS=$(jq 'length' test-results.json)
if [ "$FINDINGS" -lt 5 ]; then
    echo "❌ Expected at least 5 vulnerabilities, found $FINDINGS"
    exit 1
fi

echo "✅ Test passed - found $FINDINGS vulnerabilities"

# Cleanup
docker-compose -f /Users/mariomejia/vuln-web/docker-compose.yml down
```

### Option 2: Monitor Template Effectiveness

Track which templates are firing:

```bash
# Create a baseline
nuclei -u http://localhost:5000 \
  -tags xss,sqli,idor,auth,traversal \
  -json \
  > baseline-findings.json

# Later, after template updates, compare
nuclei -u http://localhost:5000 \
  -tags xss,sqli,idor,auth,traversal \
  -json \
  > new-findings.json

# Compare
jq -r '.[] | .template_id' baseline-findings.json | sort > baseline-templates.txt
jq -r '.[] | .template_id' new-findings.json | sort > new-templates.txt

diff baseline-templates.txt new-templates.txt
```

### Option 3: Performance Benchmarking

Measure scanner performance:

```bash
#!/bin/bash

echo "Benchmarking Rift scanner..."

# Warm up
nuclei -u http://localhost:5000 -tags xss > /dev/null 2>&1

# Time the scan
time nuclei -u http://localhost:5000 \
  -tags xss,sqli,idor,auth,traversal,exposure \
  -severity critical,high \
  -json \
  -o /tmp/benchmark-results.json

# Count findings
FINDINGS=$(jq 'length' /tmp/benchmark-results.json)
echo "Found: $FINDINGS vulnerabilities"
```

## Troubleshooting

### App won't start

```bash
# Check port 5000 is free
lsof -i :5000

# Kill process if needed
kill -9 $(lsof -t -i :5000)

# Restart
docker-compose up -d
```

### Nuclei not finding vulnerabilities

```bash
# Update nuclei templates
nuclei -update

# Run with newer templates
nuclei -u http://localhost:5000 -tags xss -v -debug
```

### Want to reset the app

```bash
# Restart containers (clears in-memory data)
docker-compose restart

# Or full rebuild
docker-compose down && docker-compose up -d --build
```

## Advanced: Customizing the Lab

Edit `app.py` to:

- Add more mock credentials (line 27-34)
- Add more vulnerable endpoints
- Change default creds (line 250)
- Add additional mock files (line 40)

Then rebuild:

```bash
docker-compose up -d --build
```

## Metrics to Track

Use this lab to measure:

| Metric | How to Check | Target |
|--------|------------|--------|
| XSS Detection Rate | nuclei tags=xss | >80% |
| SQLi Detection Rate | nuclei tags=sqli | >80% |
| IDOR Detection Rate | nuclei tags=idor | >70% |
| Info Disclosure Rate | nuclei tags=disclosure | >60% |
| False Positives | Review results.json | <5% |
| Scan Speed | time nuclei ... | <30 seconds |

## Next Steps

1. ✅ Validate that nuclei is detecting vulnerabilities
2. ✅ Compare to OWASP Top 10 coverage
3. ✅ Identify gaps in template coverage
4. ✅ Update templates as needed
5. ✅ Run periodic regression tests

---

Need help? Check the main README.md for more details.
