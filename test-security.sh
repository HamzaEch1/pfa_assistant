#!/bin/bash

# Terminal colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing HTTP to HTTPS Redirection ===${NC}"
echo "Sending request to HTTP endpoint (should redirect to HTTPS):"
REDIRECT_RESULT=$(curl -I -s http://localhost | grep -E "^HTTP|^Location")
echo "$REDIRECT_RESULT"

if [[ "$REDIRECT_RESULT" == *"301"* && "$REDIRECT_RESULT" == *"https://localhost"* ]]; then
  echo -e "${GREEN}✓ HTTP to HTTPS redirection works correctly${NC}"
else
  echo -e "${RED}✗ HTTP to HTTPS redirection failed${NC}"
fi

echo -e "\n${YELLOW}=== Testing HTTPS Endpoint ===${NC}"
echo "Sending request to HTTPS endpoint (should return 200 OK):"
HTTPS_RESULT=$(curl -I -s -k https://localhost | grep "HTTP")
echo "$HTTPS_RESULT"

if [[ "$HTTPS_RESULT" == *"200"* ]]; then
  echo -e "${GREEN}✓ HTTPS endpoint working correctly${NC}"
else
  echo -e "${RED}✗ HTTPS endpoint test failed${NC}"
fi

echo -e "\n${YELLOW}=== Testing Security Features ===${NC}"

# SQL Injection tests
echo -e "\n${YELLOW}1. SQL Injection Protection:${NC}"
SQL_TESTS=(
  "https://localhost/?query=SELECT%20*%20FROM%20users"
  "https://localhost/?id=1%20OR%201=1"
  "https://localhost/api/?query=UNION%20SELECT%20username,password%20FROM%20users"
  "https://localhost/search?term=test%27;%20DROP%20TABLE%20users;%20--"
)

for test in "${SQL_TESTS[@]}"; do
  echo "Testing: $test"
  STATUS=$(curl -o /dev/null -s -k -w "%{http_code}" "$test")
  
  if [[ "$STATUS" == "403" ]]; then
    echo -e "${GREEN}✓ Blocked (403 Forbidden)${NC}"
  else
    echo -e "${RED}✗ Not blocked (Status: $STATUS)${NC}"
  fi
done

# XSS tests
echo -e "\n${YELLOW}2. XSS Protection:${NC}"
XSS_TESTS=(
  "https://localhost/?input=%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E"
  "https://localhost/?q=%3Cimg%20src%3Dx%20onerror%3Dalert%281%29%3E"
  "https://localhost/?param=%3Ciframe%20src%3Djavascript%3Aalert%28document.cookie%29%3E"
  "https://localhost/?test=javascript%3Aalert%28%27xss%27%29"
  "https://localhost/?onclick=alert%281%29"
  "https://localhost/?param=%3Csvg%20onload%3Dalert%281%29%3E"
)

for test in "${XSS_TESTS[@]}"; do
  echo "Testing: $test"
  STATUS=$(curl -o /dev/null -s -k -w "%{http_code}" "$test")
  
  if [[ "$STATUS" == "403" ]]; then
    echo -e "${GREEN}✓ Blocked (403 Forbidden)${NC}"
  else
    echo -e "${RED}✗ Not blocked (Status: $STATUS)${NC}"
  fi
done

# Path traversal tests
echo -e "\n${YELLOW}3. Path Traversal Protection:${NC}"
PATH_TESTS=(
  "https://localhost/../../etc/passwd"
  "https://localhost/api/file?path=../../../etc/shadow"
  "https://localhost/images/../../../etc/hosts"
)

for test in "${PATH_TESTS[@]}"; do
  echo "Testing: $test"
  STATUS=$(curl -o /dev/null -s -k -w "%{http_code}" "$test")
  
  if [[ "$STATUS" == "403" ]]; then
    echo -e "${GREEN}✓ Blocked (403 Forbidden)${NC}"
  else
    echo -e "${RED}✗ Not blocked (Status: $STATUS)${NC}"
  fi
done

# Test custom error page
echo -e "\n${YELLOW}4. Custom Error Page Test:${NC}"
echo "Testing if the custom error page is displayed for blocked requests:"
ERROR_PAGE=$(curl -s -k "https://localhost/?query=SELECT%20*%20FROM%20users")

if [[ "$ERROR_PAGE" == *"Security Alert"* && "$ERROR_PAGE" == *"Request ID"* ]]; then
  echo -e "${GREEN}✓ Custom error page displayed correctly${NC}"
else
  echo -e "${RED}✗ Custom error page not displayed${NC}"
  echo "Response received:"
  echo "$ERROR_PAGE" | head -n 20
fi

echo -e "\n${YELLOW}5. Extra Edge Case Tests:${NC}"

# Test javascript: protocol directly 
echo "Testing javascript: protocol directly:"
JAVASCRIPT_TEST="https://localhost/?test=javascript:alert(1)"
STATUS=$(curl -o /dev/null -s -k -w "%{http_code}" "$JAVASCRIPT_TEST")
  
if [[ "$STATUS" == "403" ]]; then
  echo -e "${GREEN}✓ Blocked (403 Forbidden)${NC}"
else
  echo -e "${RED}✗ Not blocked (Status: $STATUS)${NC}"
fi

# Test directory traversal in path with encoding
echo "Testing encoded directory traversal:"
PATH_TRAVERSAL_TEST="https://localhost/images/..%2f..%2f/etc/passwd"
STATUS=$(curl -o /dev/null -s -k -w "%{http_code}" "$PATH_TRAVERSAL_TEST")
  
if [[ "$STATUS" == "403" ]]; then
  echo -e "${GREEN}✓ Blocked (403 Forbidden)${NC}"
else
  echo -e "${RED}✗ Not blocked (Status: $STATUS)${NC}"
fi

echo -e "\n${YELLOW}=== Security Test Complete ===${NC}" 