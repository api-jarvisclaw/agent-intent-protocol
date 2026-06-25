#!/usr/bin/env bash
# AIP — Execute intent via curl
#
# Usage:
#   export AIP_API_KEY="sk-your-key"
#   bash execute.sh

set -euo pipefail
BASE_URL="${AIP_ENDPOINT:-https://api.jarvisclaw.ai}"

echo "─── Execute: chat completion ───"
curl -s "${BASE_URL}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "chat_completion",
    "payload": {
      "messages": [{"role": "user", "content": "Explain AIP in one sentence."}],
      "max_tokens": 100
    },
    "preferences": { "optimize_for": "quality" }
  }' | python3 -m json.tool
