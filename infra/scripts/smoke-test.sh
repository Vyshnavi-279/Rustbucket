#!/usr/bin/env bash
# End-to-end smoke test against a running Rustbucket stack.
# Usage: infra/scripts/smoke-test.sh <base_url> [repo_url]
#   e.g. infra/scripts/smoke-test.sh http://localhost:8080
# The repo must have a package.json or requirements.txt in its root.
set -uo pipefail

BASE="${1:-}"
REPO="${2:-https://github.com/expressjs/express}"

if [ -z "$BASE" ]; then
  echo "Usage: $0 <base_url> [repo_url]"
  exit 2
fi
BASE="${BASE%/}"

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

fail() { echo "FAIL: $*"; exit 1; }

echo "==> 1. GET $BASE/health"
code=$(curl -s -o "$TMP" -w '%{http_code}' "$BASE/health") || fail "cannot reach $BASE"
[ "$code" = "200" ] || fail "/health returned HTTP $code"
grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"' "$TMP" || fail "/health body is not {\"status\":\"ok\"}: $(cat "$TMP")"
echo "    ok"

echo "==> 2. POST $BASE/api/scans ($REPO)"
code=$(curl -s -o "$TMP" -w '%{http_code}' -X POST "$BASE/api/scans" \
  -H 'Content-Type: application/json' -d "{\"repo_url\":\"$REPO\"}") || fail "POST request failed"
[ "$code" = "202" ] || fail "POST /api/scans returned HTTP $code (expected 202): $(cat "$TMP")"
SCAN_ID=$(grep -o '"scan_id"[[:space:]]*:[[:space:]]*[0-9]*' "$TMP" | grep -o '[0-9]*$' | head -1)
[ -n "$SCAN_ID" ] || fail "no scan_id in response: $(cat "$TMP")"
echo "    scan_id=$SCAN_ID"

echo "==> 3. Polling GET $BASE/api/scans/$SCAN_ID every 3s (max 3 minutes)"
deadline=$((SECONDS + 180))
while [ "$SECONDS" -lt "$deadline" ]; do
  code=$(curl -s -o "$TMP" -w '%{http_code}' "$BASE/api/scans/$SCAN_ID") || fail "GET request failed"
  [ "$code" = "200" ] || fail "GET /api/scans/$SCAN_ID returned HTTP $code"
  status=$(grep -o '"status"[[:space:]]*:[[:space:]]*"[a-z]*"' "$TMP" | head -1 | sed -E 's/.*"([a-z]*)"$/\1/')
  echo "    status=$status"
  case "$status" in
    done)
      score=$(grep -o '"score"[[:space:]]*:[[:space:]]*[0-9]*' "$TMP" | head -1 | grep -o '[0-9]*$')
      echo "PASS: scan finished, score=$score"
      exit 0
      ;;
    failed)
      err=$(grep -o '"error"[[:space:]]*:[[:space:]]*"[^"]*"' "$TMP" | head -1 \
        | sed -E 's/^"error"[[:space:]]*:[[:space:]]*"//; s/"$//')
      fail "scan failed: $err"
      ;;
  esac
  sleep 3
done

fail "timed out after 3 minutes"
