FROM python:3.8-slim
WORKDIR /app
COPY opendata_collector_module /app
COPY opendata_collector_module/etc/* /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
RUN apt-get update && apt-get install -y wget && \
    wget -O /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 && \
    chmod +x /usr/bin/yq
RUN mkdir -p /var/log/xroad-metrics/opendata_collector/logs
COPY Docker/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /app/bin/xroad-metrics-opendata-collector
ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-opendata-collector"]
