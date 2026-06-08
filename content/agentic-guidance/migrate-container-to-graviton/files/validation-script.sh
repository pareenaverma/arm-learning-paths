#!/bin/bash
# validation-script.sh
# Run inside the migrated container to verify it is working correctly on Arm.
# The agent runs this script at Turn 6 of the workflow.

set -e

PASS=0
FAIL=0

check() {
    local label="$1"
    local result="$2"
    if [ "$result" = "pass" ]; then
        echo "[PASS] $label"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $label"
        FAIL=$((FAIL + 1))
    fi
}

# 1. Confirm architecture is aarch64
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    check "Architecture: $ARCH" pass
else
    check "Architecture: $ARCH (expected aarch64)" fail
fi

# 2. Confirm the application process starts (adjust binary name as needed)
APP_BINARY="${APP_BINARY:-app}"
if command -v "$APP_BINARY" > /dev/null 2>&1; then
    check "Application binary found: $APP_BINARY" pass
else
    check "Application binary not found: $APP_BINARY" fail
fi

# 3. Check health endpoint if APP_PORT is set
if [ -n "$APP_PORT" ]; then
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${APP_PORT}/health" 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        check "Health endpoint HTTP $HTTP_STATUS" pass
    else
        check "Health endpoint HTTP $HTTP_STATUS (expected 200)" fail
    fi
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
