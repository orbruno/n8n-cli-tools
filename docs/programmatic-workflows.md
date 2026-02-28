# Programmatic Workflow Management

Push, update, and manage n8n workflows via the REST API without using the browser UI.

## Prerequisites

- n8n running (`docker compose up -d`)
- API key stored in `.env` as `N8N_API_KEY`

## API Key Setup

API keys are created once via the n8n UI or the internal REST endpoint.

### Option A: Via n8n UI

1. Open n8n (e.g., http://localhost:5679)
2. Go to **Settings > API**
3. Click **Create API Key**
4. Copy the key and add to `.env`:
   ```
   N8N_API_KEY=eyJhbG...your-key-here
   ```

### Option B: Via Internal REST Endpoint

```bash
# 1. Login to get session cookie
curl -c /tmp/n8n-cookies -X POST http://localhost:5679/rest/login \
  -H "Content-Type: application/json" \
  -d '{"emailOrLdapLoginId":"your@email.com","password":"your-password"}'

# 2. Create API key (expires in 1 year)
EXPIRES=$(python3 -c "import time; print(int((time.time() + 365*24*3600) * 1000))")
curl -b /tmp/n8n-cookies -X POST http://localhost:5679/rest/api-keys \
  -H "Content-Type: application/json" \
  -d "{\"label\":\"cli-access\",\"expiresAt\":${EXPIRES},\"scopes\":[\"workflow:create\",\"workflow:read\",\"workflow:update\",\"workflow:delete\",\"workflow:list\"]}"

# 3. Copy rawApiKey from the response and save to .env
```

## Pushing Workflows

### Using the Helper Script

```bash
# Push a single workflow
./push-workflow.sh workflows/my-workflow.json

# Push all workflows
./push-workflow.sh workflows/*.json
```

### Using curl Directly

The n8n API only accepts these top-level fields: `name`, `nodes`, `connections`, `settings`, `staticData`, `tags`. Extra fields like `meta` cause a rejection.

```bash
API_KEY=$(grep '^N8N_API_KEY=' .env | cut -d'=' -f2-)
N8N_PORT=$(grep '^N8N_PORT=' .env | cut -d'=' -f2-)

# Strip unsupported fields and push
python3 -c "
import json
with open('workflows/my-workflow.json') as f:
    wf = json.load(f)
payload = {
    'name': wf.get('name', 'Untitled'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': wf.get('settings', {})
}
print(json.dumps(payload))
" | curl -s -X POST "http://localhost:${N8N_PORT}/api/v1/workflows" \
    -H "X-N8N-API-KEY: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d @-
```

The response includes the workflow `id` assigned by n8n.

## Updating an Existing Workflow

```bash
WORKFLOW_ID="Efbkl19wfPYv31kp"

python3 -c "
import json
with open('workflows/calendar-digest.json') as f:
    wf = json.load(f)
payload = {
    'name': wf.get('name'),
    'nodes': wf.get('nodes', []),
    'connections': wf.get('connections', {}),
    'settings': wf.get('settings', {})
}
print(json.dumps(payload))
" | curl -s -X PUT "http://localhost:${N8N_PORT}/api/v1/workflows/${WORKFLOW_ID}" \
    -H "X-N8N-API-KEY: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d @-
```

## Listing Workflows

```bash
curl -s "http://localhost:${N8N_PORT}/api/v1/workflows" \
  -H "X-N8N-API-KEY: ${API_KEY}" | python3 -m json.tool
```

## Activating / Deactivating a Workflow

```bash
# Activate
curl -s -X POST "http://localhost:${N8N_PORT}/api/v1/workflows/${WORKFLOW_ID}/activate" \
  -H "X-N8N-API-KEY: ${API_KEY}"

# Deactivate
curl -s -X POST "http://localhost:${N8N_PORT}/api/v1/workflows/${WORKFLOW_ID}/deactivate" \
  -H "X-N8N-API-KEY: ${API_KEY}"
```

## Deleting a Workflow

```bash
curl -s -X DELETE "http://localhost:${N8N_PORT}/api/v1/workflows/${WORKFLOW_ID}" \
  -H "X-N8N-API-KEY: ${API_KEY}"
```

## Workflow JSON Structure

Workflow files in `workflows/` follow the n8n export format. The API-required subset:

```json
{
  "name": "Workflow Name",
  "nodes": [
    {
      "id": "unique-node-id",
      "name": "Node Display Name",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.2,
      "position": [200, 300],
      "parameters": { },
      "credentials": {
        "credentialType": {
          "id": "",
          "name": "Credential Name — configure in Credentials"
        }
      }
    }
  ],
  "connections": {
    "Source Node Name": {
      "main": [[{ "node": "Target Node Name", "type": "main", "index": 0 }]]
    }
  },
  "settings": {
    "executionOrder": "v1",
    "timezone": "America/Costa_Rica"
  }
}
```

**Extra fields** like `meta`, `tags`, or `id` in the root object can be included for documentation but must be stripped before pushing via the API (the `push-workflow.sh` script handles this).

## Important Notes

- **Credentials are not embedded** in workflow JSON. They reference credential IDs/names that must exist in the n8n instance. After pushing a workflow, configure credentials through the n8n UI.
- **Workflow IDs change** when re-pushing. If you push the same workflow JSON twice, it creates a duplicate. Use PUT to update an existing one.
- **The API key expires**. Check `expiresAt` in `.env` and regenerate before expiry.
- **Activation requires valid credentials**. A workflow with placeholder credential references cannot be activated until real credentials are configured.

---

Last Updated: 2026-02-23
