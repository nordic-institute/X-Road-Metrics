#!/bin/bash
set -e

# Process environment variables into settings.yaml
/entrypoint.sh true

# Start cron daemon in background
cron

# Run prepare_data.R on startup if RDS files don't exist
if [ ! -f /var/lib/xroad-metrics/networking/dat.rds ]; then
    echo "Running initial data preparation..."
    /usr/share/xroad-metrics/networking/prepare_data.R || echo "Initial data preparation failed (this is normal if PostgreSQL has no data yet)"
fi

# Start shiny-server in foreground
exec shiny-server
