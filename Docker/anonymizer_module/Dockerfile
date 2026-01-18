FROM python:3.8-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        wget \
    && wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 \
    && chmod +x /usr/bin/yq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY anonymizer_module/ ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY Docker/docker-entrypoint.sh /entrypoint.sh

RUN mkdir -p /var/log/xroad-metrics/anonymizer/logs /var/run/xroad-metrics \
    && mkdir -p /etc/xroad-metrics/anonymizer \
    && cp /app/etc/field_data.yaml /etc/xroad-metrics/anonymizer/ \
    && cp /app/etc/field_translations.list /etc/xroad-metrics/anonymizer/ \
    && ln -s /app/etc/settings.yaml /app/settings.yaml \
    && chmod +x /app/bin/xroad-metrics-anonymizer /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-anonymizer"]
