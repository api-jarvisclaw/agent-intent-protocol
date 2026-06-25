#!/usr/bin/env bash
# AIP — Resolve intent via curl
#
# Usage:
#   export AIP_API_KEY="sk-your-key"
#   bash resolve.sh

set -euo pipefail
BASE_URL="${AIP_ENDPOINT:-https://api.jarvisclaw.ai}"

echo "─── Resolve: cheapest chat completion ───"
curl -s "${BASE_URL}/v1/intent/resolve" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "chat_completion",
    "constraints": { "max_price_usd": 0.01 },
    "preferences": { "optimize_for": "cost" }
  }' | python3 -m json.tool
