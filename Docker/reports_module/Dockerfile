# =============================================================================
# Base Stage - Common setup for all X-Road Metrics modules
# =============================================================================
FROM python:3.8-slim AS metrics-base

ARG YQ_VERSION=4.43.1

RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64 \
    && chmod +x /usr/bin/yq \
    && apt-get purge -y wget \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --system --group --no-create-home xroad-metrics

COPY Docker/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app

# =============================================================================
# Runtime Stage
# =============================================================================
FROM metrics-base AS runtime

# Install runtime dependencies for PDF rendering
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi8 \
        libcairo2 \
        libxml2 \
        libxslt1.1 \
        fonts-liberation \
        fonts-dejavu-core \
        libpangoft2-1.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY reports_module/ ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip setuptools wheel \
    && rm -rf /usr/local/lib/python*/site-packages/pip* \
              /usr/local/lib/python*/site-packages/setuptools* \
              /usr/local/lib/python*/site-packages/wheel* \
    && find /usr/local/lib/python*/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python*/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

RUN mkdir -p /var/log/xroad-metrics/reports/logs /var/run/xroad-metrics \
    && mkdir -p /etc/xroad-metrics/reports /var/lib/xroad-metrics/reports \
    && cp -r /app/etc/lang /etc/xroad-metrics/reports/ \
    && cp -r /app/etc/template /etc/xroad-metrics/reports/ \
    && ln -s /app/etc/settings.yaml /app/settings.yaml \
    && chown -R xroad-metrics:xroad-metrics /var/log/xroad-metrics /var/run/xroad-metrics \
       /etc/xroad-metrics/reports /var/lib/xroad-metrics/reports /app \
    && chmod +x /app/bin/xroad-metrics-reports

USER xroad-metrics

ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-reports"]
