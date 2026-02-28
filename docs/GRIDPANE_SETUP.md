# n8n Setup on GridPane (Nginx + SSL)

This guide documents the steps required to deploy n8n on a GridPane-managed VPS using nginx as a reverse proxy with Let's Encrypt SSL.

## Prerequisites

- GridPane VPS with nginx installed
- Docker installed (snap version)
- Domain with DNS access
- SSH root access

## Issues Encountered & Solutions

### 1. Snap Docker Path Restrictions

**Problem**: The snap version of Docker cannot access `/opt` due to sandboxing restrictions.

```bash
# This fails with snap Docker:
docker compose -f /opt/docker-n8n-stack/docker-compose.yml up -d
# Error: open /opt/docker-n8n-stack/docker-compose.yml: no such file or directory
```

**Solution**: Copy the project to the home directory, which snap Docker can access via the `home` interface.

```bash
cp -r /opt/docker-n8n-stack ~/docker-n8n-stack
cd ~/docker-n8n-stack
docker compose up -d
```

### 2. Port 80 Conflict with Nginx

**Problem**: The production docker-compose includes Traefik for SSL termination, but GridPane already uses nginx on ports 80/443.

```bash
# Traefik fails to start:
# Error: failed to bind host port for 0.0.0.0:80 - address already in use
```

**Solution**: Use nginx as the reverse proxy instead of Traefik.

```bash
# Remove the Traefik container
docker rm -f traefik

# Use only the base docker-compose (without docker-compose.prod.yml)
docker compose up -d
```

### 3. Owner Account Cannot Be Automated

**Problem**: n8n v1.0+ requires manual setup of the owner account via the web interface. Environment variables like `N8N_DEFAULT_USER_EMAIL` and `N8N_DEFAULT_USER_PASSWORD` do not work.

**Solution**: Accept that this step must be done manually after deployment. Document it clearly.

## Step-by-Step Setup

### Step 1: Copy Project to Home Directory

```bash
cp -r /opt/docker-n8n-stack ~/docker-n8n-stack
cd ~/docker-n8n-stack
```

### Step 2: Configure Environment

Edit `.env` with your production settings:

```bash
# .env
N8N_ENCRYPTION_KEY=<generate with: openssl rand -hex 32>
N8N_HOST=n8n.yourdomain.com
N8N_PORT=5678
N8N_PROTOCOL=https
WEBHOOK_URL=https://n8n.yourdomain.com/
TIMEZONE=America/Costa_Rica
```

### Step 3: Start Docker Containers

```bash
# Start n8n and cli-tools (without Traefik)
docker compose up -d

# Verify containers are running
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE                            STATUS         PORTS
xxxx           docker.n8n.io/n8nio/n8n:latest   Up X minutes   0.0.0.0:5678->5678/tcp
xxxx           cli-tools:latest                 Up X minutes
```

### Step 4: Create DNS Record

Add an A record pointing your subdomain to the server IP:

| Type | Name | Value |
|------|------|-------|
| A | n8n | YOUR_SERVER_IP |

Verify DNS propagation:
```bash
dig n8n.yourdomain.com +short
```

### Step 5: Create Nginx Configuration

Create `/etc/nginx/sites-available/n8n.yourdomain.com`:

```nginx
# n8n Reverse Proxy Configuration
# Domain: n8n.yourdomain.com -> localhost:5678

server {
    listen 80;
    listen [::]:80;
    server_name n8n.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name n8n.yourdomain.com;

    # SSL certificates (populated by certbot)
    ssl_certificate /etc/letsencrypt/live/n8n.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/n8n.yourdomain.com/privkey.pem;

    # Logging
    access_log /var/log/nginx/n8n.yourdomain.com.access.log;
    error_log /var/log/nginx/n8n.yourdomain.com.error.log;

    # Proxy to n8n
    location / {
        proxy_pass http://127.0.0.1:5678;
        proxy_http_version 1.1;

        # WebSocket support (required for n8n)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;

        # Timeouts for long-running workflows
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;

        # Buffer settings
        proxy_buffering off;

        # Max body size for file uploads
        client_max_body_size 100M;
    }
}
```

**Important for GridPane**: Do not include custom `ssl_session_cache` directives as GridPane already defines these globally and nginx will throw a conflict error.

### Step 6: Get SSL Certificate

First, enable the site with a temporary HTTP-only config for certbot validation:

```bash
# Create webroot directory
mkdir -p /var/www/html

# Enable site (temporarily without SSL block, or certbot will fail)
ln -sf /etc/nginx/sites-available/n8n.yourdomain.com /etc/nginx/sites-enabled/

# Test nginx config
nginx -t

# Reload nginx
systemctl reload nginx
```

Get the certificate:

```bash
certbot certonly \
  --webroot \
  -w /var/www/html \
  -d n8n.yourdomain.com \
  --non-interactive \
  --agree-tos \
  --email your@email.com
```

Expected output:
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/n8n.yourdomain.com/fullchain.pem
Key is saved at: /etc/letsencrypt/live/n8n.yourdomain.com/privkey.pem
```

### Step 7: Enable Full Configuration

```bash
# Test nginx config
nginx -t

# Reload nginx
systemctl reload nginx
```

### Step 8: Verify Setup

```bash
# Check n8n is accessible
curl -sI https://n8n.yourdomain.com | head -3
```

Expected output:
```
HTTP/2 200
date: ...
content-type: text/html; charset=utf-8
```

### Step 9: Create Owner Account

1. Open `https://n8n.yourdomain.com` in your browser
2. Fill in the owner account setup form:
   - First name
   - Last name
   - Email
   - Password
3. Click "Next" to complete setup

> **Note**: This step cannot be automated. As of n8n v1.0+, an owner account is mandatory and must be created via the web interface.

## Nginx Configuration Notes for GridPane

GridPane uses a specific nginx configuration structure. Key points:

1. **Use `http2 on;` directive** instead of the deprecated `listen ... http2` syntax
2. **Do not define `ssl_session_cache`** - GridPane defines this globally
3. **Do not define custom SSL protocols/ciphers** unless necessary - GridPane handles this
4. **Use standard logging paths**: `/var/log/nginx/domain.access.log`

### Common Nginx Errors

**Error**: `the size X of shared memory zone "SSL" conflicts with already declared size Y`

**Solution**: Remove any `ssl_session_cache` directives from your site config.

**Error**: `the "listen ... http2" directive is deprecated`

**Solution**: Change from:
```nginx
listen 443 ssl http2;
```
To:
```nginx
listen 443 ssl;
http2 on;
```

## Maintenance

### Restart n8n

```bash
cd ~/docker-n8n-stack
docker compose restart n8n
```

### View Logs

```bash
# n8n logs
docker logs -f n8n

# nginx logs
tail -f /var/log/nginx/n8n.yourdomain.com.error.log
```

### Update n8n

```bash
cd ~/docker-n8n-stack
docker compose pull n8n
docker compose up -d
```

### Renew SSL Certificate

Certbot automatically renews certificates. To manually renew:

```bash
certbot renew
systemctl reload nginx
```

### Reset Owner Account

If you need to reset the owner account:

```bash
docker exec -it n8n n8n user-management:reset
docker restart n8n
```

Then visit the web interface to create a new owner account.

## File Locations

| File | Path |
|------|------|
| Docker Compose | `~/docker-n8n-stack/docker-compose.yml` |
| Environment | `~/docker-n8n-stack/.env` |
| Nginx config | `/etc/nginx/sites-available/n8n.yourdomain.com` |
| SSL certificate | `/etc/letsencrypt/live/n8n.yourdomain.com/` |
| n8n data | Docker volume `n8n_data` |
| Nginx access log | `/var/log/nginx/n8n.yourdomain.com.access.log` |
| Nginx error log | `/var/log/nginx/n8n.yourdomain.com.error.log` |

## References

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Docker Installation](https://docs.n8n.io/hosting/installation/docker/)
- [n8n CLI Commands](https://docs.n8n.io/hosting/cli-commands/)
- [GridPane Documentation](https://gridpane.com/kb/)
- [Certbot Documentation](https://certbot.eff.org/docs/)

---

**Last Updated**: 2026-02-04
