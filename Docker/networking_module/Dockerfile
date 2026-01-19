FROM rocker/shiny:4.5.2

ARG YQ_VERSION=4.43.1

# Install system dependencies, yq, and cleanup
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        odbc-postgresql \
        libglpk40 \
        cron \
        wget \
    && wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64 \
    && chmod +x /usr/bin/yq \
    && apt-get purge -y wget \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# Create xroad-metrics user
RUN groupadd -r xroad-metrics && useradd -r -g xroad-metrics xroad-metrics

# Create all directories
RUN mkdir -p /var/log/xroad-metrics/networking/logs \
             /var/log/xroad-metrics/networking/heartbeat \
             /var/lib/xroad-metrics/networking \
             /etc/xroad-metrics/networking \
             /usr/share/xroad-metrics/networking/shiny/www \
             /var/log/shiny-server

# Copy all networking module files
COPY networking_module/prepare_data.R /usr/share/xroad-metrics/networking/
COPY networking_module/prepare_data_settings.R /usr/share/xroad-metrics/networking/
COPY networking_module/networking-cron-entrypoint.sh /usr/share/xroad-metrics/networking/
COPY networking_module/app.R /usr/share/xroad-metrics/networking/shiny/
COPY networking_module/www/ /usr/share/xroad-metrics/networking/shiny/www/
COPY networking_module/etc/settings.yaml /etc/xroad-metrics/networking/
COPY networking_module/etc/shiny-server/shiny-server.conf /etc/shiny-server/
COPY networking_module/etc/cron.d/xroad-metrics-networking-cron /etc/cron.d/
COPY Docker/docker-entrypoint.sh /entrypoint.sh
COPY Docker/networking_module/startup.sh /startup.sh

# Set permissions and create symlink
RUN chmod +x /usr/share/xroad-metrics/networking/prepare_data.R \
             /usr/share/xroad-metrics/networking/networking-cron-entrypoint.sh \
             /entrypoint.sh \
             /startup.sh \
    && chmod 0644 /etc/cron.d/xroad-metrics-networking-cron \
    && ln -s /usr/share/xroad-metrics/networking/prepare_data.R /usr/bin/xroad-metrics-networking \
    && chown -R xroad-metrics:xroad-metrics /var/log/xroad-metrics/networking \
                                            /var/lib/xroad-metrics/networking \
                                            /usr/share/xroad-metrics/networking \
                                            /var/log/shiny-server

# Set environment variable for entrypoint to find settings
ENV METRICS_SETTINGS_FILE=/etc/xroad-metrics/networking/settings.yaml

EXPOSE 3838
CMD ["/startup.sh"]
