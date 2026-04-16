#!/bin/bash

###############################################
# Rift Scanner Test Lab - Vulnerability Test
# Tests all vulnerabilities in the app
###############################################

set -e

BASE_URL="http://localhost:5000"
RESULTS_FILE="/tmp/rift-vuln-test-results.txt"

echo "==================================="
echo "Rift Scanner Test Lab - Test Suite"
echo "==================================="
echo ""

# Check if app is running
echo "🔍 Checking if app is running at $BASE_URL..."
if ! curl -s "$BASE_URL" > /dev/null; then
    echo "❌ App is not running at $BASE_URL"
    echo "Start with: docker-compose up -d"
    exit 1
fi
echo "✅ App is running!"
echo ""

# Clear results file
> "$RESULTS_FILE"

# Test 1: Home page
echo "📋 Test 1: Home Page"
echo "---"
curl -s "$BASE_URL" | head -20
echo "✅ Home page accessible"
echo "" | tee -a "$RESULTS_FILE"

# Test 2: Reflected XSS
echo "🔴 Test 2: Reflected XSS"
echo "---"
XSS_PAYLOAD="<script>alert('xss')</script>"
RESPONSE=$(curl -s "$BASE_URL/xss/reflected?q=$XSS_PAYLOAD")
if echo "$RESPONSE" | grep -q "$XSS_PAYLOAD"; then
    echo "✅ Reflected XSS VULNERABLE - Payload echoed back without sanitization"
    echo "Test 2: Reflected XSS - VULNERABLE" >> "$RESULTS_FILE"
else
    echo "❌ Reflected XSS not found"
fi
echo ""

# Test 3: Stored XSS
echo "🔴 Test 3: Stored XSS"
echo "---"
curl -s -X POST "$BASE_URL/xss/stored" \
  -d "name=testuser&comment=<img src=x onerror=alert('stored_xss')>" \
  > /dev/null
RESPONSE=$(curl -s "$BASE_URL/xss/stored")
if echo "$RESPONSE" | grep -q "onerror"; then
    echo "✅ Stored XSS VULNERABLE - Comment stored and executed"
    echo "Test 3: Stored XSS - VULNERABLE" >> "$RESULTS_FILE"
else
    echo "❌ Stored XSS not found"
fi
echo ""

# Test 4: Path Traversal
echo "🔴 Test 4: Path Traversal"
echo "---"
for FILE in "config.yaml" "secrets.env" "debug.log" "users.json" "backup.sql"; do
    RESPONSE=$(curl -s "$BASE_URL/files?file=$FILE")
    if echo "$RESPONSE" | grep -q "mock\|Mock\|MOCK"; then
        echo "✅ Path Traversal VULNERABLE - Accessed $FILE"
        echo "Test 4: Path Traversal ($FILE) - VULNERABLE" >> "$RESULTS_FILE"
    fi
done
echo ""

# Test 5: SQL Injection
echo "🔴 Test 5: SQL Injection"
echo "---"
RESPONSE=$(curl -s "$BASE_URL/search?q=' OR '1'='1")
if echo "$RESPONSE" | grep -q "admin\|user1\|user2"; then
    echo "✅ SQL Injection VULNERABLE - Query returns all users"
    echo "Test 5: SQL Injection - VULNERABLE" >> "$RESULTS_FILE"
else
    echo "❌ SQL Injection payload didn't work as expected"
fi
echo ""

# Test 6: IDOR
echo "🔴 Test 6: IDOR (Insecure Direct Object Reference)"
echo "---"
for UID in 1 2 3; do
    RESPONSE=$(curl -s "$BASE_URL/user/$UID")
    if echo "$RESPONSE" | grep -q "Password"; then
        echo "✅ IDOR VULNERABLE - Accessed user $UID without authorization"
        echo "Test 6: IDOR (User $UID) - VULNERABLE" >> "$RESULTS_FILE"
    fi
done
echo ""

# Test 7: Default Credentials
echo "🔴 Test 7: Default Credentials"
echo "---"
RESPONSE=$(curl -s -X POST "$BASE_URL/login" \
  -d "username=admin&password=admin123")
if echo "$RESPONSE" | grep -q "Login Successful\|Session ID"; then
    echo "✅ Default Credentials VULNERABLE - admin/admin123 works"
    echo "Test 7: Default Credentials - VULNERABLE" >> "$RESULTS_FILE"
else
    echo "❌ Default credentials failed"
fi
echo ""

# Test 8: Sensitive Data Exposure
echo "🔴 Test 8: Sensitive Data Exposure"
echo "---"
echo "Testing /api/debug endpoint..."
RESPONSE=$(curl -s "$BASE_URL/api/debug")
if echo "$RESPONSE" | grep -q "api_key\|api_secret\|database"; then
    echo "✅ Sensitive Data Exposure VULNERABLE - Debug endpoint leaks secrets"
    echo "Test 8: Sensitive Data Exposure (/api/debug) - VULNERABLE" >> "$RESULTS_FILE"
fi

echo "Testing /api/config endpoint..."
RESPONSE=$(curl -s "$BASE_URL/api/config")
if echo "$RESPONSE" | grep -q "password\|secret"; then
    echo "✅ Sensitive Data Exposure VULNERABLE - Config endpoint leaks credentials"
    echo "Test 8: Sensitive Data Exposure (/api/config) - VULNERABLE" >> "$RESULTS_FILE"
fi
echo ""

# Test 9: Information Disclosure
echo "🔴 Test 9: Information Disclosure"
echo "---"
RESPONSE=$(curl -s "$BASE_URL/robots.txt")
if echo "$RESPONSE" | grep -q "admin\|api"; then
    echo "✅ Information Disclosure VULNERABLE - robots.txt exposes paths"
    echo "Test 9: Information Disclosure (robots.txt) - VULNERABLE" >> "$RESULTS_FILE"
fi

RESPONSE=$(curl -s "$BASE_URL/sitemap.xml")
if echo "$RESPONSE" | grep -q "url\|loc"; then
    echo "✅ Information Disclosure VULNERABLE - sitemap.xml exposes paths"
    echo "Test 9: Information Disclosure (sitemap.xml) - VULNERABLE" >> "$RESULTS_FILE"
fi
echo ""

# Test 10: Nuclei Integration (if nuclei is installed)
echo "🔴 Test 10: Nuclei Scanner Integration"
echo "---"
if command -v nuclei &> /dev/null; then
    echo "Running nuclei scan..."
    nuclei -u "$BASE_URL" \
      -tags xss,sqli,idor,auth,default-login,exposure,disclosure \
      -severity critical,high \
      -timeout 5 \
      -json \
      -o /tmp/nuclei-test-results.json 2>/dev/null || true

    if [ -f "/tmp/nuclei-test-results.json" ] && [ -s "/tmp/nuclei-test-results.json" ]; then
        FINDING_COUNT=$(cat /tmp/nuclei-test-results.json | jq 'length')
        echo "✅ Nuclei found $FINDING_COUNT vulnerabilities"
        echo "Test 10: Nuclei Integration - Found $FINDING_COUNT vulnerabilities" >> "$RESULTS_FILE"

        # Show template breakdown
        echo ""
        echo "Vulnerabilities by type:"
        cat /tmp/nuclei-test-results.json | jq -r '.[] | .info.name' | sort | uniq -c
    else
        echo "⚠️  Nuclei ran but found 0 vulnerabilities (might need template updates)"
    fi
else
    echo "⚠️  Nuclei not installed - skipping nuclei integration test"
fi
echo ""

# Summary
echo "==================================="
echo "📊 Test Summary"
echo "==================================="
cat "$RESULTS_FILE"
echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""
echo "✅ All vulnerability tests completed!"
echo ""
echo "Next steps:"
echo "1. Review findings in $RESULTS_FILE"
echo "2. Run: nuclei -u http://localhost:5000 -tags xss,sqli,idor -v"
echo "3. Integrate with your Rift scanner for validation"
