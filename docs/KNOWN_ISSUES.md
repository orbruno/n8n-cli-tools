# n8n Known Issues & Troubleshooting

## n8n Shows "Create New User" Instead of Login Screen

**Date Encountered**: 2025-12-02
**Affected Instances**: n8n__Job-Search

**Symptoms**:
- n8n displays the initial setup/create new user screen
- Existing user account is not recognized
- Database exists with user data but appears inaccessible

**Root Cause**:
n8n requires an encryption key (`N8N_ENCRYPTION_KEY`) to decrypt user credentials stored in the database. When this key is missing or doesn't match the one originally used, n8n cannot read the existing user data and defaults to showing the setup screen.

**Solution**:

1. Locate the encryption key in the n8n data directory:
   ```bash
   cat ./n8n_data/config
   ```
   The key is stored in the `encryptionKey` field.

2. Add the encryption key to `compose.yaml` as an environment variable:
   ```yaml
   services:
     n8n:
       environment:
         - N8N_ENCRYPTION_KEY=<your-encryption-key-here>
   ```

3. **Important**: Restart is not enough - must recreate the container:
   ```bash
   docker compose up -d --force-recreate n8n
   ```

   **Note**: `docker compose restart` does NOT reload environment variables.

4. Verify the key is loaded:
   ```bash
   docker compose exec n8n env | grep N8N_ENCRYPTION_KEY
   ```

**Instance-Specific Details**:

### n8n__Job-Search
- **Encryption Key**: `0io5WSpI6wuIiabn1qyC1B1ObZOMvJSt` (stored in `./n8n_data/config`)
- **User**: orbruno@gmail.com (Orlando Bruno)
- **User ID**: 0283af0f-0381-456a-9890-f92359c15670
- **Data Directory**: `./n8n_data` (active, 1.3 GB database)

---

## Useful Commands

```bash
# Check if user exists in database
sqlite3 ./n8n_data/database.sqlite "SELECT id, email, firstName, lastName FROM user;"

# View encryption key
cat ./n8n_data/config

# Recreate container after config changes
docker compose up -d --force-recreate n8n

# View logs
docker compose logs n8n --tail 50

# Verify environment variables in container
docker compose exec n8n env | grep N8N_
```

---

Last Updated: 2025-12-02
