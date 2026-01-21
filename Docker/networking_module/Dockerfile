FROM rocker/shiny:4.3.2

# Install system dependencies for ODBC, PostgreSQL, and GLPK (for igraph)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        odbc-postgresql \
        libglpk40 \
        cron \
        wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install yq for settings processing
RUN wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.43.1/yq_linux_amd64 \
    && chmod +x /usr/bin/yq

# Install R packages needed by networking module
RUN install2.r --error \
    dplyr \
    shinycssloaders \
    ggplot2 \
    qgraph \
    igraph \
    jsonlite \
    yaml \
    RODBC

# Create xroad-metrics user (matching Debian package)
RUN groupadd -r xroad-metrics && useradd -r -g xroad-metrics xroad-metrics

# Create directories (matching Debian package structure)
RUN mkdir -p /var/log/xroad-metrics/networking/logs \
    && mkdir -p /var/log/xroad-metrics/networking/heartbeat \
    && mkdir -p /var/lib/xroad-metrics/networking \
    && mkdir -p /etc/xroad-metrics/networking \
    && mkdir -p /usr/share/xroad-metrics/networking/shiny/www \
    && mkdir -p /var/log/shiny-server

# Copy R scripts for data preparation (matching Debian package paths)
COPY networking_module/prepare_data.R /usr/share/xroad-metrics/networking/
COPY networking_module/prepare_data_settings.R /usr/share/xroad-metrics/networking/
COPY networking_module/networking-cron-entrypoint.sh /usr/share/xroad-metrics/networking/
RUN chmod +x /usr/share/xroad-metrics/networking/prepare_data.R \
    && chmod +x /usr/share/xroad-metrics/networking/networking-cron-entrypoint.sh

# Create symlink matching Debian package
RUN ln -s /usr/share/xroad-metrics/networking/prepare_data.R /usr/bin/xroad-metrics-networking

# Copy Shiny app (matching Debian package paths)
COPY networking_module/app.R /usr/share/xroad-metrics/networking/shiny/
COPY networking_module/www/ /usr/share/xroad-metrics/networking/shiny/www/

# Copy config files from etc/ (matching Debian package)
COPY networking_module/etc/settings.yaml /etc/xroad-metrics/networking/
COPY networking_module/etc/shiny-server/shiny-server.conf /etc/shiny-server/
COPY networking_module/etc/cron.d/xroad-metrics-networking-cron /etc/cron.d/
RUN chmod 0644 /etc/cron.d/xroad-metrics-networking-cron

# Set environment variable for entrypoint to find settings
ENV METRICS_SETTINGS_FILE=/etc/xroad-metrics/networking/settings.yaml

# Copy entrypoint and startup scripts
COPY Docker/docker-entrypoint.sh /entrypoint.sh
COPY Docker/networking_module/startup.sh /startup.sh
RUN chmod +x /entrypoint.sh /startup.sh

# Set permissions
RUN chown -R xroad-metrics:xroad-metrics /var/log/xroad-metrics/networking \
    && chown -R xroad-metrics:xroad-metrics /var/lib/xroad-metrics/networking \
    && chown -R xroad-metrics:xroad-metrics /usr/share/xroad-metrics/networking \
    && chown -R xroad-metrics:xroad-metrics /var/log/shiny-server

EXPOSE 3838
CMD ["/startup.sh"]
