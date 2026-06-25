#!/usr/bin/env bash
# AIP — Discover available intents and providers via curl
#
# Usage:
#   export AIP_API_KEY="sk-your-key"
#   bash discover.sh

set -euo pipefail
BASE_URL="${AIP_ENDPOINT:-https://api.jarvisclaw.ai}"

echo "─── List available intents ───"
curl -s "${BASE_URL}/v1/intent/list" \
  -H "Authorization: Bearer ${AIP_API_KEY}" | python3 -m json.tool

echo ""
echo "─── Providers for chat_completion ───"
curl -s "${BASE_URL}/v1/intent/providers?intent=chat_completion" \
  -H "Authorization: Bearer ${AIP_API_KEY}" | python3 -m json.tool
