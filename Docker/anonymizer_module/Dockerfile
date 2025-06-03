FROM python:3.8-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev wget && \
    wget -O /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 && \
    chmod +x /usr/bin/yq && \
    rm -rf /var/lib/apt/lists/*
COPY anonymizer_module /app
COPY anonymizer_module/etc/* /app/
RUN mkdir -p /var/log/xroad-metrics/anonymizer/logs
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
COPY Docker/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /app/bin/xroad-metrics-anonymizer
ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-anonymizer"]
