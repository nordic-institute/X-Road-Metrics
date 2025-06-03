FROM python:3.8-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev wget apache2 libapache2-mod-wsgi-py3 && \
    wget -O /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 && \
    chmod +x /usr/bin/yq && \
    rm -rf /var/lib/apt/lists/*
COPY opendata_module /app
COPY opendata_module/etc/* /app/
RUN mkdir -p /var/log/xroad-metrics/opendata/logs
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
COPY Docker/docker-entrypoint.sh /entrypoint.sh
# Remove the line that sets permissions on a non-existent binary
# RUN chmod +x /app/bin/metrics_opendata
# Copy Apache config
COPY Docker/opendata_module/apache-opendata.conf /etc/apache2/sites-available/000-default.conf
# Ensure static files directory exists
RUN mkdir -p /app/opmon_opendata/static
# Enable mod_wsgi (already installed)
RUN a2enmod wsgi
# Set entrypoint to our script, which will exec apache2ctl
ENTRYPOINT ["/entrypoint.sh"]
# Set CMD to start Apache in foreground if no arguments are passed
CMD ["apache2ctl", "-D", "FOREGROUND"]
