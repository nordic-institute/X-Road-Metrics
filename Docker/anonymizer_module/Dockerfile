ARG BASE_IMAGE=set-via-prepare-containers.sh

# =============================================================================
# Builder Stage - Compile Python dependencies
# =============================================================================
FROM ${BASE_IMAGE} AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY anonymizer_module/ ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# =============================================================================
# Anonymizer Module
# =============================================================================
FROM ${BASE_IMAGE} AS runtime

# Install runtime library for PostgreSQL
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels \
    && pip uninstall -y pip setuptools wheel \
    && rm -rf /usr/local/lib/python*/site-packages/pip* \
              /usr/local/lib/python*/site-packages/setuptools* \
              /usr/local/lib/python*/site-packages/wheel* \
    && find /usr/local/lib/python*/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python*/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

COPY anonymizer_module/ ./

RUN mkdir -p /var/log/xroad-metrics/anonymizer/logs /var/run/xroad-metrics \
    && mkdir -p /etc/xroad-metrics/anonymizer \
    && cp /app/etc/field_data.yaml /etc/xroad-metrics/anonymizer/ \
    && cp /app/etc/field_translations.list /etc/xroad-metrics/anonymizer/ \
    && ln -s /app/etc/settings.yaml /app/settings.yaml \
    && chown -R xroad-metrics:xroad-metrics /var/log/xroad-metrics /var/run/xroad-metrics \
       /etc/xroad-metrics/anonymizer /app \
    && chmod +x /app/bin/xroad-metrics-anonymizer

USER xroad-metrics

ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-anonymizer"]
