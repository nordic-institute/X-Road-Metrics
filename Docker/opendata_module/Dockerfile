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
COPY opendata_module/ ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# =============================================================================
# OpenData Module
# =============================================================================
FROM ${BASE_IMAGE} AS runtime

# Install runtime libraries for PostgreSQL and Apache
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        apache2 \
        libapache2-mod-wsgi-py3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add www-data to xroad-metrics group to access files through group membership
RUN usermod -aG xroad-metrics www-data

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels \
    && pip uninstall -y pip setuptools wheel \
    && rm -rf /usr/local/lib/python*/site-packages/pip* \
              /usr/local/lib/python*/site-packages/setuptools* \
              /usr/local/lib/python*/site-packages/wheel* \
    && find /usr/local/lib/python*/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python*/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

COPY opendata_module/ ./
COPY Docker/opendata_module/apache-opendata.conf /etc/apache2/sites-available/000-default.conf

RUN mkdir -p /var/log/xroad-metrics/opendata/logs /var/log/xroad-metrics/opendata/heartbeat \
    && mkdir -p /var/run/xroad-metrics /app/opmon_opendata/static \
    && mkdir -p /etc/xroad-metrics/opendata \
    && cp /app/etc/field_data.yaml /etc/xroad-metrics/opendata/ \
    && ln -s /app/etc/settings.yaml /app/settings.yaml \
    && chown -R xroad-metrics:xroad-metrics /var/log/xroad-metrics/opendata \
                                            /var/run/xroad-metrics \
                                            /app \
                                            /etc/xroad-metrics/opendata \
    && chmod -R g+rwx /var/log/xroad-metrics/opendata \
                      /var/run/xroad-metrics \
                      /app \
                      /etc/xroad-metrics/opendata \
    && a2enmod wsgi

# Skip log redirect to stdout - Apache WSGI runs as www-data and can't write to /dev/stdout symlinks
ENV SKIP_LOG_REDIRECT=1

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2ctl", "-D", "FOREGROUND"]
