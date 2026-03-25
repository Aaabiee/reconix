#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "Scanning staged files for secrets..."

PATTERNS=(
  'AKIA[0-9A-Z]{16}'
  'sk_live_[a-zA-Z0-9]+'
  'ghp_[a-zA-Z0-9]{36}'
  'glpat-[a-zA-Z0-9-]+'
  'xox[bpsa]-[a-zA-Z0-9-]+'
  'BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY'
  'password\s*[:=]\s*["\x27][^"\x27]{12,}["\x27]'
)

FOUND=0
for pattern in "${PATTERNS[@]}"; do
  MATCHES=$(git diff --cached --diff-filter=ACM -G "$pattern" --name-only 2>/dev/null || true)
  if [ -n "$MATCHES" ]; then
    echo -e "${RED}POTENTIAL SECRET DETECTED (pattern: $pattern):${NC}"
    echo "$MATCHES" | while read -r file; do
      echo "  $file"
    done
    FOUND=1
  fi
done

BLOCKED_FILES=$(git diff --cached --name-only | grep -iE '\.(pem|key|crt|p12|pfx|jks|env)$' 2>/dev/null | grep -v '\.example$' || true)
if [ -n "$BLOCKED_FILES" ]; then
  echo -e "${RED}BLOCKED FILE TYPES DETECTED:${NC}"
  echo "$BLOCKED_FILES" | while read -r file; do
    echo "  $file"
  done
  FOUND=1
fi

if [ "$FOUND" -eq 1 ]; then
  echo -e "${RED}COMMIT BLOCKED: Remove secrets before committing.${NC}"
  exit 1
fi

echo -e "${GREEN}No secrets detected. Safe to commit.${NC}"
