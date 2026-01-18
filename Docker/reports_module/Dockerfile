FROM python:3.8-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        wget \
        libpango-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        libcairo2 \
        libxml2 \
        libxslt1.1 \
        fonts-liberation \
        fonts-dejavu-core \
        libpangoft2-1.0-0 \
    && wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 \
    && chmod +x /usr/bin/yq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY reports_module/ ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY Docker/docker-entrypoint.sh /entrypoint.sh

RUN adduser --system --group --no-create-home xroad-metrics \
    && mkdir -p /var/log/xroad-metrics/reports/logs /var/run/xroad-metrics \
    && mkdir -p /etc/xroad-metrics/reports /var/lib/xroad-metrics/reports \
    && cp -r /app/etc/lang /etc/xroad-metrics/reports/ \
    && cp -r /app/etc/template /etc/xroad-metrics/reports/ \
    && ln -s /app/etc/settings.yaml /app/settings.yaml \
    && chown -R xroad-metrics:xroad-metrics /app /var/log/xroad-metrics /var/run/xroad-metrics \
       /etc/xroad-metrics/reports /var/lib/xroad-metrics/reports \
    && chmod +x /app/bin/xroad-metrics-reports /entrypoint.sh

USER xroad-metrics

ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-reports"]
