FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        wget \
        apache2 \
        libapache2-mod-wsgi-py3 \
    && wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 \
    && chmod +x /usr/bin/yq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY opendata_module/ ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY Docker/docker-entrypoint.sh /entrypoint.sh
COPY Docker/opendata_module/apache-opendata.conf /etc/apache2/sites-available/000-default.conf

RUN mkdir -p /var/log/xroad-metrics/opendata/logs /var/log/xroad-metrics/opendata/heartbeat \
    && mkdir -p /var/run/xroad-metrics /app/opmon_opendata/static \
    && mkdir -p /etc/xroad-metrics/opendata \
    && cp /app/etc/field_data.yaml /etc/xroad-metrics/opendata/ \
    && ln -s /app/etc/settings.yaml /app/settings.yaml \
    && chown -R www-data:www-data /var/log/xroad-metrics/opendata \
    && a2enmod wsgi \
    && chmod +x /entrypoint.sh

# Skip log redirect to stdout - Apache WSGI runs as www-data and can't write to /dev/stdout symlinks
ENV SKIP_LOG_REDIRECT=1

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
# Set CMD to start Apache in foreground if no arguments are passed
CMD ["apache2ctl", "-D", "FOREGROUND"]
