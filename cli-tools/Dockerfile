# CLI Tools Docker Image
# Contains: web-scraper-cli, mdconvert-cli, imagen-cli, qr-gen-cli, dbt
#
# Build: docker build -t cli-tools .
# Run:   docker run -it cli-tools
# Update: docker run -it cli-tools update-cli-tools

FROM python:3.11-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Git for cloning repos
    git \
    # Node.js for web-scraper-cli (Puppeteer)
    nodejs \
    npm \
    # Puppeteer dependencies
    chromium \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    # WeasyPrint dependencies for mdconvert-cli
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Pandoc for mdconvert-cli DOCX support
    pandoc \
    # PostgreSQL client for dbt
    postgresql-client \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Set Puppeteer to use system Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Install UV package manager
RUN pip install --no-cache-dir uv

# Create directory for CLI tools
WORKDIR /opt/cli-tools

# Clone all repositories (using HTTPS for easy updates)
RUN git clone https://github.com/orbruno/web-scraper-cli.git && \
    git clone https://github.com/orbruno/mdconvert-cli.git && \
    git clone https://github.com/orbruno/image-cli.git imagen-cli && \
    git clone https://github.com/orbruno/qr-gen-cli.git && \
    git clone https://github.com/orbruno/dbt-cli.git

# Install web-scraper-cli
WORKDIR /opt/cli-tools/web-scraper-cli
RUN uv sync && \
    cd scraper && npm install

# Install mdconvert-cli
WORKDIR /opt/cli-tools/mdconvert-cli
RUN uv sync

# Install imagen-cli
WORKDIR /opt/cli-tools/imagen-cli
RUN uv sync

# Install qr-gen-cli
WORKDIR /opt/cli-tools/qr-gen-cli
RUN uv sync

# Install dbt-cli (dbt-postgres and dbt-bigquery)
WORKDIR /opt/cli-tools/dbt-cli
RUN uv sync

# Create wrapper scripts for global access
RUN mkdir -p /usr/local/bin

# webscrape wrapper
RUN echo '#!/bin/bash\ncd /opt/cli-tools/web-scraper-cli && uv run webscrape "$@"' > /usr/local/bin/webscrape && \
    chmod +x /usr/local/bin/webscrape

# mdconvert wrapper
RUN echo '#!/bin/bash\ncd /opt/cli-tools/mdconvert-cli && uv run mdconvert "$@"' > /usr/local/bin/mdconvert && \
    chmod +x /usr/local/bin/mdconvert

# md2pdf wrapper (alias for mdconvert)
RUN echo '#!/bin/bash\ncd /opt/cli-tools/mdconvert-cli && uv run md2pdf "$@"' > /usr/local/bin/md2pdf && \
    chmod +x /usr/local/bin/md2pdf

# genimg wrapper
RUN echo '#!/bin/bash\ncd /opt/cli-tools/imagen-cli && uv run genimg "$@"' > /usr/local/bin/genimg && \
    chmod +x /usr/local/bin/genimg

# qrgen wrapper
RUN echo '#!/bin/bash\ncd /opt/cli-tools/qr-gen-cli && uv run qrgen "$@"' > /usr/local/bin/qrgen && \
    chmod +x /usr/local/bin/qrgen

# dbt wrapper
RUN echo '#!/bin/bash\ncd /opt/cli-tools/dbt-cli && uv run dbt "$@"' > /usr/local/bin/dbt && \
    chmod +x /usr/local/bin/dbt

# Create update script to pull latest changes from all repos
RUN echo '#!/bin/bash\n\
echo "Updating CLI tools from GitHub..."\n\
\n\
for tool in web-scraper-cli mdconvert-cli imagen-cli qr-gen-cli dbt-cli; do\n\
    echo ""\n\
    echo "==> Updating $tool"\n\
    cd /opt/cli-tools/$tool\n\
    git pull origin main\n\
    uv sync\n\
    if [ "$tool" = "web-scraper-cli" ]; then\n\
        cd scraper && npm install\n\
    fi\n\
done\n\
\n\
echo ""\n\
echo "All CLI tools updated!"' > /usr/local/bin/update-cli-tools && \
    chmod +x /usr/local/bin/update-cli-tools

# Copy and set up entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set working directory for user
WORKDIR /workspace

# Create a help script for the default command
RUN echo '#!/bin/bash\n\
echo "CLI Tools Docker Image"\n\
echo "======================"\n\
echo ""\n\
echo "Available commands:"\n\
echo "  webscrape  - Scrape files from JavaScript-heavy pages"\n\
echo "  mdconvert  - Convert Markdown to PDF or DOCX"\n\
echo "  md2pdf     - Alias for mdconvert"\n\
echo "  genimg     - Generate images with Google Imagen API"\n\
echo "  qrgen      - Generate branded QR codes"\n\
echo "  dbt        - Data transformation with dbt (PostgreSQL/BigQuery)"\n\
echo ""\n\
echo "Update tools:"\n\
echo "  update-cli-tools  - Pull latest from GitHub and reinstall"\n\
echo ""\n\
echo "Run with: docker run -it cli-tools <command>"\n\
echo "Interactive: docker run -it cli-tools bash"' > /usr/local/bin/cli-tools-help && \
    chmod +x /usr/local/bin/cli-tools-help

# Entrypoint handles auto-update checks
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command shows available tools
CMD ["/usr/local/bin/cli-tools-help"]
