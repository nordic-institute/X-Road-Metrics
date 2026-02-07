#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../config/env.sh"
source "$SCRIPT_DIR/../helpers/common.sh"

DISTRO="${1:?Usage: $0 <distro> <db-versions>}"
DB_VERSIONS="${2:?Usage: $0 <distro> <db-versions>}"
CONTAINER_NAME="${CONTAINER_PREFIX}-${DISTRO}"

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------

# Ensure clean environment
"$HELPERS_DIR/setup/ensure-clean-env.sh" "$DISTRO"

# Provision container
"$HELPERS_DIR/setup/provision-lxd-container.sh" "$DISTRO"

# Start databases
"$HELPERS_DIR/setup/start-dbs.sh" "$DB_VERSIONS"

[ "${XROAD_MODE:-mock}" = "mock" ] && \
    docker compose -f "$DOCKER_DIR/docker-compose.mock-xroad.yml" up -d --wait

# Install old packages from artifactory (init scripts come from the .deb packages)
"$HELPERS_DIR/setup/install-metrics-from-artifactory.sh" "$CONTAINER_NAME"

# Initialize database users (uses xroad-metrics-init-mongo + xroad-metrics-init-postgresql)
"$HELPERS_DIR/setup/create-db-users.sh" "$CONTAINER_NAME"

# Configure modules
"$HELPERS_DIR/setup/configure-modules.sh" "$CONTAINER_NAME"

# Run full cycle test
"$HELPERS_DIR/run-pipeline.sh" "$CONTAINER_NAME"

# Save counts before upgrade
"$HELPERS_DIR/data-counts.sh" save pre-upgrade

# Stop services before upgrade
info "Stopping services for upgrade..."
lxc exec "$CONTAINER_NAME" -- bash -c "
    systemctl stop xroad-metrics-opendata 2>/dev/null || true
    systemctl stop cron 2>/dev/null || true
"

# Install new packages (same script as fresh install)
"$HELPERS_DIR/setup/install-metrics.sh" "$CONTAINER_NAME" "$DISTRO"

# Start services after upgrade
info "Starting services after upgrade..."
lxc exec "$CONTAINER_NAME" -- bash -c "
    systemctl start cron 2>/dev/null || true
    systemctl start xroad-metrics-opendata 2>/dev/null || true
"

# Run full cycle test
"$HELPERS_DIR/run-pipeline.sh" "$CONTAINER_NAME"

# Verify no data loss
"$HELPERS_DIR/data-counts.sh" verify pre-upgrade
