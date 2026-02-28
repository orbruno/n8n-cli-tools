# Notion API Setup for n8n

Connect Notion databases and pages to n8n workflows.

## Prerequisites

- A Notion account with admin access to the workspace

## Step 1: Create a Notion Integration

1. Go to [My Integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Fill in:
   - Name: `n8n`
   - Associated workspace: select your workspace
   - Type: **Internal**
4. Click **Submit**
5. Copy the **Internal Integration Secret** (starts with `ntn_` or `secret_`)

## Step 2: Share Pages/Databases with the Integration

Notion integrations can only access pages explicitly shared with them.

1. Open the Notion page or database you want n8n to access
2. Click **...** (three dots) in the top-right > **Connections**
3. Search for your integration name (`n8n`) and click **Confirm**
4. Repeat for every page/database n8n needs to access

## Step 3: Add Credential to n8n

1. Open n8n at `http://localhost:5678`
2. Go to **Credentials > Add Credential**
3. Search for **Notion API**
4. Choose **Internal Integration Token** method
5. Paste your Internal Integration Secret
6. Click **Save**

## Step 4: Test the Connection

1. Create a new workflow
2. Add a **Notion** node
3. Select your Notion credential
4. Set resource to **Database** and operation to **Get Many**
5. Select a database from the dropdown (only shared databases appear)
6. Execute the node — you should see your database entries

## Common Use Cases

| Workflow | Description |
|----------|-------------|
| Gmail → Notion | Save important emails as Notion pages |
| Notion → Calendar | Sync Notion deadlines to Google Calendar |
| Schedule → Notion | Daily summary of database changes |
| Notion → Slack/Telegram | Notify when database entries change |

## Troubleshooting

### "Could not find database"

The database isn't shared with your integration. Go to the Notion database > **...** > **Connections** > add your integration.

### "API token is not valid"

Re-copy the token from [My Integrations](https://www.notion.so/my-integrations). Make sure you're using the **Internal Integration Secret**, not the integration ID.

---

**Related**: [n8n Notion docs](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.notion/)
