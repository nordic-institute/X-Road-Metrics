# =============================================================================
# X-Road Metrics Base Image
# Common foundation for all Python-based X-Road Metrics modules
# =============================================================================

ARG PYTHON_VERSION=3.8-slim

FROM python:${PYTHON_VERSION}

ARG YQ_VERSION=4.43.1

# Install yq for YAML configuration manipulation
RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64 \
    && chmod +x /usr/bin/yq \
    && apt-get purge -y wget \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for running modules
RUN adduser --system --group --no-create-home xroad-metrics

# Copy shared entrypoint script
COPY Docker/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app
