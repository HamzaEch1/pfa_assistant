#!/bin/bash

# Terminal colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing Strict Path Traversal Detection ===${NC}"

# Array of path traversal test cases with various encodings
TESTS=(
  "https://localhost/images/../../../etc/hosts"
  "https://localhost/images/..%2f..%2f..%2fetc/hosts"
  "https://localhost/images/..%252f..%252f..%252fetc/hosts"
  "https://localhost/..%255c..%255c/etc/hosts"
  "https://localhost/images%2f..%2f..%2f..%2fetc%2fhosts"
  "https://localhost/images/../etc/../../hosts"
)

for test in "${TESTS[@]}"; do
  echo -e "\nTesting: ${test}"
  STATUS=$(curl -o /dev/null -s -k -w "%{http_code}" "$test")
  
  if [[ "$STATUS" == "403" ]]; then
    echo -e "${GREEN}✓ Blocked (403 Forbidden)${NC}"
  else
    echo -e "${RED}✗ Not blocked (Status: $STATUS)${NC}"
    
    # Show response content for non-403 responses
    echo "Response content:"
    curl -s -k "$test" | head -n 5
  fi
done

echo -e "\n${YELLOW}=== Test Complete ===${NC}" 