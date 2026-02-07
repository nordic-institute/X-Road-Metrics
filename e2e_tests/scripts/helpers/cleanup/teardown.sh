#!/bin/bash
# Remove all E2E test containers (LXD and Docker)
#
# Usage: teardown.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

teardown_lxd() {
    info "Removing LXD containers (prefix: $CONTAINER_PREFIX)..."
    CONTAINERS=$(lxc list --format csv -c n | grep "^${CONTAINER_PREFIX}" || true)
    if [ -z "$CONTAINERS" ]; then
        info "  No LXD containers found."
    else
        for container in $CONTAINERS; do
            info "  Removing: $container"
            lxc delete "$container" --force
        done
    fi
}

teardown_docker() {
    info "Removing Docker containers..."
    docker compose -f "$DOCKER_DIR/docker-compose.mock-xroad.yml" down -v
    docker compose -f "$DOCKER_DIR/docker-compose.dbs.yml" down -v
}

teardown_lxd
teardown_docker

success "Cleanup complete."
