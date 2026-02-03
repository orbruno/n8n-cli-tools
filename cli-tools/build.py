#!/usr/bin/env python3
"""
CLI Tools Docker Builder

Reads cli-tools.yml configuration and builds a Docker image
with only the specified tools.

Usage:
    python build.py                     # Build with default config
    python build.py --config custom.yml # Build with custom config
    python build.py --dry-run           # Generate Dockerfile without building
    python build.py --list              # List available tools
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


# Dependency mappings
DEPENDENCY_PACKAGES = {
    "nodejs": ["nodejs", "npm"],
    "chromium": [
        "chromium",
        "fonts-liberation",
        "libasound2",
        "libatk-bridge2.0-0",
        "libatk1.0-0",
        "libcups2",
        "libdbus-1-3",
        "libdrm2",
        "libgbm1",
        "libgtk-3-0",
        "libnspr4",
        "libnss3",
        "libx11-xcb1",
        "libxcomposite1",
        "libxdamage1",
        "libxfixes3",
        "libxrandr2",
        "xdg-utils",
    ],
    "weasyprint": [
        "libpango-1.0-0",
        "libpangocairo-1.0-0",
        "libgdk-pixbuf2.0-0",
        "libffi-dev",
        "shared-mime-info",
    ],
    "pandoc": ["pandoc"],
}


def load_config(config_path: Path) -> dict:
    """Load and validate configuration file."""
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    return config


def get_enabled_tools(config: dict) -> dict:
    """Get only enabled tools from config."""
    return {
        name: tool
        for name, tool in config.get("tools", {}).items()
        if tool.get("enabled", True)
    }


def collect_packages(tools: dict, base_packages: list) -> list:
    """Collect all required apt packages."""
    packages = set(base_packages)

    for tool in tools.values():
        for req in tool.get("requires", []):
            if req in DEPENDENCY_PACKAGES:
                packages.update(DEPENDENCY_PACKAGES[req])
            else:
                # Assume it's a direct apt package name
                packages.add(req)

    return sorted(packages)


def generate_dockerfile(config: dict) -> str:
    """Generate Dockerfile content from configuration."""
    base = config.get("base", {})
    python_version = base.get("python_version", "3.11")
    tools = get_enabled_tools(config)
    base_packages = config.get("system_packages", ["git"])
    packages = collect_packages(tools, base_packages)

    # Check if nodejs/chromium is needed
    needs_chromium = any(
        "chromium" in tool.get("requires", []) for tool in tools.values()
    )

    lines = [
        f"# Auto-generated Dockerfile from cli-tools.yml",
        f"# Tools: {', '.join(tools.keys())}",
        f"",
        f"FROM python:3.11-slim-bookworm",
        f"",
        f"# Install system dependencies",
        f"RUN apt-get update && apt-get install -y --no-install-recommends \\",
    ]

    # Add packages
    for i, pkg in enumerate(packages):
        if i < len(packages) - 1:
            lines.append(f"    {pkg} \\")
        else:
            lines.append(f"    {pkg} \\")
    lines.append("    && rm -rf /var/lib/apt/lists/*")
    lines.append("")

    # Chromium environment variables
    if needs_chromium:
        lines.extend([
            "# Set Puppeteer to use system Chromium",
            "ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true",
            "ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium",
            "",
        ])

    # Install UV
    lines.extend([
        "# Install UV package manager",
        "RUN pip install --no-cache-dir uv",
        "",
        "# Create directory for CLI tools",
        "WORKDIR /opt/cli-tools",
        "",
    ])

    # Clone repositories
    lines.append("# Clone repositories")
    clone_commands = []
    for name, tool in tools.items():
        repo = tool["repo"]
        local_name = tool.get("local_name", name)
        if local_name != name:
            clone_commands.append(f"git clone {repo} {local_name}")
        else:
            clone_commands.append(f"git clone {repo}")

    lines.append("RUN " + " && \\\n    ".join(clone_commands))
    lines.append("")

    # Install each tool
    for name, tool in tools.items():
        local_name = tool.get("local_name", name)
        lines.extend([
            f"# Install {name}",
            f"WORKDIR /opt/cli-tools/{local_name}",
            f"RUN uv sync",
        ])
        if tool.get("post_install"):
            lines.append(f"RUN {tool['post_install']}")
        lines.append("")

    # Create wrapper scripts
    lines.extend([
        "# Create wrapper scripts for global access",
        "RUN mkdir -p /usr/local/bin",
        "",
    ])

    for name, tool in tools.items():
        local_name = tool.get("local_name", name)
        command = tool["command"]

        # Main command
        lines.append(f"# {command} wrapper")
        lines.append(
            f"RUN echo '#!/bin/bash\\ncd /opt/cli-tools/{local_name} && uv run {command} \"$@\"' "
            f"> /usr/local/bin/{command} && \\"
        )
        lines.append(f"    chmod +x /usr/local/bin/{command}")
        lines.append("")

        # Aliases
        for alias in tool.get("aliases", []):
            lines.append(f"# {alias} wrapper (alias for {command})")
            lines.append(
                f"RUN echo '#!/bin/bash\\ncd /opt/cli-tools/{local_name} && uv run {alias} \"$@\"' "
                f"> /usr/local/bin/{alias} && \\"
            )
            lines.append(f"    chmod +x /usr/local/bin/{alias}")
            lines.append("")

    # Create update script
    tool_names = [tool.get("local_name", name) for name, tool in tools.items()]
    update_script_lines = [
        '#!/bin/bash',
        'echo "Updating CLI tools from GitHub..."',
        '',
    ]
    for name, tool in tools.items():
        local_name = tool.get("local_name", name)
        update_script_lines.extend([
            'echo ""',
            f'echo "==> Updating {local_name}"',
            f'cd /opt/cli-tools/{local_name}',
            'git pull origin main',
            'uv sync',
        ])
        if tool.get("post_install"):
            update_script_lines.append(tool["post_install"])

    update_script_lines.extend([
        'echo ""',
        'echo "All CLI tools updated!"',
    ])

    lines.append("# Create update script")
    lines.append("RUN echo '" + "\\n".join(update_script_lines).replace("'", "'\\''") + "' > /usr/local/bin/update-cli-tools && \\")
    lines.append("    chmod +x /usr/local/bin/update-cli-tools")
    lines.append("")

    # Create help script
    help_lines = [
        'echo "CLI Tools Docker Image"',
        'echo "======================"',
        'echo ""',
        'echo "Available commands:"',
    ]
    for name, tool in tools.items():
        cmd = tool["command"]
        desc = tool.get("description", "")
        help_lines.append(f'echo "  {cmd:12} - {desc}"')
        for alias in tool.get("aliases", []):
            help_lines.append(f'echo "  {alias:12} - Alias for {cmd}"')

    help_lines.extend([
        'echo ""',
        'echo "Update tools:"',
        'echo "  update-cli-tools  - Pull latest from GitHub and reinstall"',
        'echo ""',
        'echo "Run with: docker run -it IMAGE_NAME <command>"',
        'echo "Interactive: docker run -it IMAGE_NAME bash"',
    ])

    lines.append("# Create help script")
    lines.append("RUN echo '#!/bin/bash\\n" + "\\n".join(help_lines) + "' > /usr/local/bin/cli-tools-help && \\")
    lines.append("    chmod +x /usr/local/bin/cli-tools-help")
    lines.append("")

    # Copy entrypoint script
    lines.extend([
        "# Copy and set up entrypoint script for auto-updates",
        "COPY entrypoint.sh /usr/local/bin/entrypoint.sh",
        "RUN chmod +x /usr/local/bin/entrypoint.sh",
        "",
    ])

    # Set working directory and default command
    lines.extend([
        "# Set working directory for user",
        "WORKDIR /workspace",
        "",
        "# Entrypoint handles auto-update checks",
        'ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]',
        "",
        "# Default command shows available tools",
        'CMD ["/usr/local/bin/cli-tools-help"]',
        "",
    ])

    return "\n".join(lines)


def build_image(dockerfile_content: str, image_name: str, image_tag: str) -> bool:
    """Build Docker image from generated Dockerfile."""
    dockerfile_path = Path("Dockerfile.generated")

    # Write generated Dockerfile
    dockerfile_path.write_text(dockerfile_content)
    print(f"Generated Dockerfile: {dockerfile_path}")

    # Build image
    full_tag = f"{image_name}:{image_tag}"
    print(f"\nBuilding Docker image: {full_tag}")
    print("=" * 50)

    try:
        result = subprocess.run(
            ["docker", "build", "-t", full_tag, "-f", str(dockerfile_path), "."],
            check=True,
        )
        print("=" * 50)
        print(f"Successfully built: {full_tag}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code: {e.returncode}")
        return False


def list_tools(config: dict) -> None:
    """List all available tools and their status."""
    tools = config.get("tools", {})

    print("Available CLI Tools:")
    print("=" * 60)
    print(f"{'Tool':<20} {'Enabled':<10} {'Command':<15} {'Description'}")
    print("-" * 60)

    for name, tool in tools.items():
        enabled = "Yes" if tool.get("enabled", True) else "No"
        command = tool.get("command", "N/A")
        description = tool.get("description", "")[:30]
        print(f"{name:<20} {enabled:<10} {command:<15} {description}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Build CLI Tools Docker image from configuration"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("cli-tools.yml"),
        help="Configuration file (default: cli-tools.yml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate Dockerfile without building",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available tools",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Dockerfile.generated"),
        help="Output Dockerfile path (default: Dockerfile.generated)",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # List tools
    if args.list:
        list_tools(config)
        return

    # Get enabled tools
    tools = get_enabled_tools(config)
    if not tools:
        print("No tools enabled in configuration!")
        sys.exit(1)

    print(f"Enabled tools: {', '.join(tools.keys())}")

    # Generate Dockerfile
    dockerfile_content = generate_dockerfile(config)

    if args.dry_run:
        # Just write the Dockerfile
        args.output.write_text(dockerfile_content)
        print(f"\nGenerated Dockerfile: {args.output}")
        print("\nTo build manually:")
        print(f"  docker build -t cli-tools -f {args.output} .")
    else:
        # Build the image
        base = config.get("base", {})
        image_name = base.get("image_name", "cli-tools")
        image_tag = base.get("image_tag", "latest")
        build_image(dockerfile_content, image_name, image_tag)


if __name__ == "__main__":
    main()
