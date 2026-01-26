ARG BASE_IMAGE=set-via-prepare-containers.sh

# =============================================================================
# Corrector Module
# =============================================================================
FROM ${BASE_IMAGE} AS runtime

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
