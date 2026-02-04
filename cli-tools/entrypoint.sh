#!/bin/bash
# CLI Tools Entrypoint Script
# Optionally checks for updates before running commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Auto-update settings (controlled by environment variables)
AUTO_UPDATE=${CLI_TOOLS_AUTO_UPDATE:-false}
UPDATE_CHECK=${CLI_TOOLS_UPDATE_CHECK:-false}

check_for_updates() {
    local tool_dir="$1"
    local tool_name=$(basename "$tool_dir")

    cd "$tool_dir"

    # Fetch latest without merging
    git fetch origin main --quiet 2>/dev/null || return 1

    # Check if we're behind
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}[UPDATE AVAILABLE]${NC} $tool_name"
        return 0
    fi
    return 1
}

update_tool() {
    local tool_dir="$1"
    local tool_name=$(basename "$tool_dir")

    echo -e "${GREEN}Updating${NC} $tool_name..."
    cd "$tool_dir"

    git pull origin main --quiet
    uv sync --quiet

    # Run post-install if it's web-scraper-cli
    if [ "$tool_name" = "web-scraper-cli" ] && [ -d "scraper" ]; then
        cd scraper && npm install --silent
    fi

    echo -e "${GREEN}✓${NC} $tool_name updated"
}

# Check/update tools if enabled
if [ "$AUTO_UPDATE" = "true" ] || [ "$UPDATE_CHECK" = "true" ]; then
    echo "Checking for updates..."

    updates_available=false

    # Check all CLI tool directories including dbt-cli
    for tool_dir in /opt/cli-tools/*/; do
        if [ -d "$tool_dir/.git" ]; then
            if check_for_updates "$tool_dir"; then
                updates_available=true

                if [ "$AUTO_UPDATE" = "true" ]; then
                    update_tool "$tool_dir"
                fi
            fi
        fi
    done

    if [ "$updates_available" = "false" ]; then
        echo -e "${GREEN}All tools are up to date${NC}"
    elif [ "$UPDATE_CHECK" = "true" ] && [ "$AUTO_UPDATE" != "true" ]; then
        echo ""
        echo -e "${YELLOW}Updates available. Run with CLI_TOOLS_AUTO_UPDATE=true to auto-update${NC}"
        echo -e "Or run: ${GREEN}update-cli-tools${NC}"
    fi

    echo ""
fi

# Execute the command passed to the container
exec "$@"
