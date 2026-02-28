#!/bin/bash
# Push a workflow JSON file to the n8n instance via API
#
# Usage:
#   ./push-workflow.sh workflows/my-workflow.json
#   ./push-workflow.sh workflows/*.json     # push all

set -e

# Load API key from .env
if [ -f .env ]; then
    API_KEY=$(grep '^N8N_API_KEY=' .env | cut -d'=' -f2-)
fi

if [ -z "$API_KEY" ]; then
    echo "Error: N8N_API_KEY not found in .env"
    exit 1
fi

# Get n8n port from .env or default
N8N_PORT=$(grep '^N8N_PORT=' .env | cut -d'=' -f2- || echo "5678")
BASE_URL="http://localhost:${N8N_PORT}"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <workflow.json> [workflow2.json ...]"
    exit 1
fi

for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "Skip: $file (not found)"
        continue
    fi

    name=$(python3 -c "import json; print(json.load(open('$file')).get('name','Untitled'))")

    result=$(python3 -c "
import json, sys
with open('$file') as f:
    wf = json.load(f)
payload = {
    'name': wf.get('name', 'Untitled'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': wf.get('settings', {})
}
print(json.dumps(payload))
" | curl -s -X POST "${BASE_URL}/api/v1/workflows" \
      -H "X-N8N-API-KEY: ${API_KEY}" \
      -H "Content-Type: application/json" \
      -d @-)

    wf_id=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)

    if [ -n "$wf_id" ]; then
        echo "OK: ${name} — ID: ${wf_id}"
    else
        echo "FAIL: ${name} — $(echo "$result" | head -c 200)"
    fi
done
