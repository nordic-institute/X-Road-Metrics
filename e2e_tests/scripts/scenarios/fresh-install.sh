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

# Install packages (init scripts come from the .deb packages, so install first)
"$HELPERS_DIR/setup/install-metrics.sh" "$CONTAINER_NAME" "$DISTRO"

# Initialize database users (uses xroad-metrics-init-mongo + xroad-metrics-init-postgresql)
"$HELPERS_DIR/setup/create-db-users.sh" "$CONTAINER_NAME"

# Configure modules
"$HELPERS_DIR/setup/configure-modules.sh" "$CONTAINER_NAME"

# Run tests
"$HELPERS_DIR/run-pipeline.sh" "$CONTAINER_NAME"
