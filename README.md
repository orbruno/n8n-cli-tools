# n8n + CLI Tools

Docker Compose setup for running n8n workflow automation with integrated CLI tools.

Supports both **development** (local) and **production** (Traefik/SSL) modes.

## Features

- **n8n** - Workflow automation platform
- **CLI Tools** - webscrape, mdconvert, genimg, qrgen
- **Development mode** - Local access on port 5678
- **Production mode** - Traefik reverse proxy with automatic SSL
- **Shared volumes** - File exchange between n8n and CLI tools
- **Auto-updates** - CLI tools can update from GitHub on container start

## Quick Start

### Development (Local)

```bash
# Clone repository
git clone https://github.com/orbruno/n8n-cli-tools.git
cd n8n-cli-tools

# Run setup (generates secure credentials)
./setup.sh

# Start services
docker-compose up -d

# Access n8n
open http://localhost:5678
```

### Production (With SSL)

```bash
# Run production setup
./setup.sh --prod

# Start with Traefik
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Access n8n at your configured domain
# https://n8n.yourdomain.com
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                          │
│                                                              │
│  ┌────────────┐     ┌──────────────┐     ┌───────────────┐  │
│  │  Traefik   │────>│     n8n      │────>│   cli-tools   │  │
│  │  (prod)    │     │   :5678      │exec │  webscrape    │  │
│  │  :80/:443  │     │              │     │  mdconvert    │  │
│  └────────────┘     └──────────────┘     │  genimg       │  │
│                            │             │  qrgen        │  │
│                            │             └───────────────┘  │
│                     ┌──────┴──────┐             │           │
│                     │   shared    │─────────────┘           │
│                     │   /data     │                         │
│                     └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Using CLI Tools in n8n

### Execute Command Node

In n8n's **Execute Command** node:

```bash
# Scrape website
docker exec cli-tools webscrape scrape "{{ $json.url }}" -o /data/shared/

# Convert Markdown to PDF
docker exec cli-tools mdconvert /files/document.md /data/shared/output.pdf

# Generate QR code
docker exec cli-tools qrgen "{{ $json.url }}" -o /data/shared/qr.png

# Generate AI image (requires GOOGLE_AI_API_KEY)
docker exec cli-tools genimg "{{ $json.prompt }}" -o /data/shared/image.png
```

### Shared Volumes

| Volume | n8n Path | cli-tools Path | Purpose |
|--------|----------|----------------|---------|
| shared_data | `/data/shared` | `/data/shared` | Output files |
| local-files | `/files` | `/files` | Host-mounted files |

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `N8N_ADMIN_USER` | Admin username | Yes |
| `N8N_ADMIN_PASSWORD` | Admin password | Yes |
| `N8N_ENCRYPTION_KEY` | Encryption key | Yes |
| `DOMAIN_NAME` | Domain (production) | Prod only |
| `SUBDOMAIN` | Subdomain (production) | Prod only |
| `SSL_EMAIL` | Let's Encrypt email | Prod only |
| `GOOGLE_AI_API_KEY` | For imagen-cli | Optional |

### Customize CLI Tools

Edit `cli-tools/cli-tools.yml` to enable/disable tools:

```yaml
tools:
  web-scraper-cli:
    enabled: true
  imagen-cli:
    enabled: false  # Disable if not needed
```

Rebuild after changes:
```bash
docker-compose build cli-tools
docker-compose up -d
```

## Commands

```bash
# Development
docker-compose up -d                    # Start
docker-compose down                     # Stop
docker-compose logs -f n8n              # View n8n logs

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Update n8n
docker-compose pull n8n
docker-compose up -d

# Update CLI tools
docker exec cli-tools update-cli-tools

# Access CLI tools container
docker exec -it cli-tools bash
```

## Directory Structure

```
n8n-cli-tools/
├── docker-compose.yml        # Base configuration
├── docker-compose.prod.yml   # Production (Traefik/SSL)
├── .env.example              # Environment template
├── setup.sh                  # Interactive setup script
├── cli-tools/                # CLI tools Docker build
│   ├── Dockerfile
│   ├── cli-tools.yml         # Tool configuration
│   └── entrypoint.sh
├── workflows/                # Exported n8n workflows
├── local-files/              # Host-mounted files
└── docs/
    └── KNOWN_ISSUES.md       # Troubleshooting guide
```

## Troubleshooting

See [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) for common issues.

### Quick Fixes

```bash
# n8n shows setup screen instead of login
# → Encryption key mismatch. Check docs/KNOWN_ISSUES.md

# CLI tools not executing
docker exec -it cli-tools bash
webscrape --help

# Check shared volume
docker exec n8n ls -la /data/shared
docker exec cli-tools ls -la /data/shared
```

## Related Repositories

- [cli-tools](https://github.com/orbruno/cli-tools) - CLI Tools Docker image
- [web-scraper-cli](https://github.com/orbruno/web-scraper-cli)
- [mdconvert-cli](https://github.com/orbruno/mdconvert-cli)
- [image-cli](https://github.com/orbruno/image-cli) (imagen-cli)
- [qr-gen-cli](https://github.com/orbruno/qr-gen-cli)

---

**Last Updated**: 2026-02-03
