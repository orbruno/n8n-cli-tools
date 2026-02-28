# Google OAuth2 Setup for n8n

Connect Gmail, Google Calendar, and Google Drive to n8n using OAuth2.

## Prerequisites

- A Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## Step 1: Create a GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown (top-left) > **New Project**
3. Name it (e.g., `n8n-automations`) > **Create**
4. Select the new project from the dropdown

## Step 2: Enable APIs

Go to **APIs & Services > Library** and enable:

- **Gmail API** — `https://console.cloud.google.com/apis/library/gmail.googleapis.com`
- **Google Calendar API** — `https://console.cloud.google.com/apis/library/calendar-json.googleapis.com`
- **Google Drive API** — `https://console.cloud.google.com/apis/library/drive.googleapis.com`

Click **Enable** for each.

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** (or Internal if using Google Workspace)
3. Fill in:
   - App name: `n8n`
   - User support email: your email
   - Developer contact email: your email
4. Click **Save and Continue**
5. **Scopes**: Add the scopes for Gmail, Calendar, and Drive (or skip — n8n requests scopes at connection time)
6. **Test users**: Add your Google email address
7. **Save and Continue** through the remaining steps

## Step 4: Create OAuth2 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **+ Create Credentials > OAuth client ID**
3. Application type: **Web application**
4. Name: `n8n`
5. **Authorized redirect URIs** — Add:

   | Environment | Redirect URI |
   |-------------|-------------|
   | Development | `http://localhost:5678/rest/oauth2-credential/callback` |
   | Production  | `https://n8n.yourdomain.com/rest/oauth2-credential/callback` |

6. Click **Create**
7. Copy the **Client ID** and **Client Secret**

## Step 5: Add Credentials to n8n

### Option A: Via Environment Variables

Add to your `.env` file (or run `./setup.sh`):

```
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

### Option B: Via n8n UI (Recommended)

1. Open n8n at `http://localhost:5678`
2. Go to **Credentials > Add Credential**
3. Search for **Google OAuth2 API**
4. Paste your Client ID and Client Secret
5. Click **Connect** — a Google sign-in window opens
6. Authorize n8n to access your Google account
7. The credential is now saved and ready to use in workflows

## Step 6: Test the Connection

1. Create a new workflow
2. Add a **Gmail** node
3. Select your Google OAuth2 credential
4. Set operation to **Get Many** (messages)
5. Execute the node — you should see your recent emails

## Troubleshooting

### "Error 400: redirect_uri_mismatch"

The redirect URI in GCP doesn't match your n8n URL. Verify:
- `N8N_EDITOR_BASE_URL` and `WEBHOOK_URL` in `.env` match your access URL
- The redirect URI in GCP matches exactly: `{your-n8n-url}/rest/oauth2-credential/callback`

### "Access blocked: app not verified"

Your OAuth consent screen is in testing mode. Make sure your email is listed as a test user.

### OAuth window doesn't appear

Check that `N8N_EDITOR_BASE_URL` is set correctly. This URL is used to generate the OAuth redirect.

---

**Related**: [n8n Google OAuth2 docs](https://docs.n8n.io/integrations/builtin/credentials/google/oauth-single-service/)
