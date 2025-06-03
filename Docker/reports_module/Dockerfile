FROM python:3.8-slim
WORKDIR /app
COPY reports_module /app
COPY reports_module/etc/* /app/
RUN apt-get update && apt-get install -y \
    wget \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    libxml2 \
    libxslt1.1 \
    fonts-liberation \
    fonts-dejavu-core \
    libpangoft2-1.0-0 \
    && wget -O /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 \
    && chmod +x /usr/bin/yq
RUN mkdir -p /var/log/xroad-metrics/reports/logs
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
COPY Docker/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /app/bin/xroad-metrics-reports
ENTRYPOINT ["/entrypoint.sh", "/app/bin/xroad-metrics-reports"]
