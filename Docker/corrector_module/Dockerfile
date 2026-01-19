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

COPY corrector_module/ ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip setuptools wheel \
    && rm -rf /usr/local/lib/python*/site-packages/pip* \
              /usr/local/lib/python*/site-packages/setuptools* \
              /usr/local/lib/python*/site-packages/wheel* \
    && find /usr/local/lib/python*/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python*/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

RUN mkdir -p /var/log/xroad-metrics/corrector/logs /var/run/xroad-metrics \
    && ln -s /app/etc/settings.yaml /app/settings.yaml \
    && chown -R xroad-metrics:xroad-metrics /var/log/xroad-metrics /var/run/xroad-metrics /app \
    && chmod +x /app/bin/xroad-metrics-correctord

USER xroad-metrics

ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-correctord"]
