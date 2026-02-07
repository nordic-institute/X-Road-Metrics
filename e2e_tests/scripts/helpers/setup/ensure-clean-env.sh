#!/bin/bash
# Ensure clean environment before running tests
#
# Checks for existing LXD and Docker containers. If any exist,
# prompts user to clean up or exits with error.
#
# Usage: ensure-clean-env.sh <distro>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

DISTRO="${1:?Distro required}"
LXD_CONTAINER="${CONTAINER_PREFIX}-${DISTRO}"

check_existing() {
    EXISTING=""

    if lxc info "$LXD_CONTAINER" &>/dev/null; then
        EXISTING="$EXISTING  - LXD container: $LXD_CONTAINER\n"
    fi

    if docker ps -a --format '{{.Names}}' | grep -q "^${MONGO_DOCKER_CONTAINER}$"; then
        EXISTING="$EXISTING  - Docker container: $MONGO_DOCKER_CONTAINER\n"
    fi

    if docker ps -a --format '{{.Names}}' | grep -q "^${POSTGRES_DOCKER_CONTAINER}$"; then
        EXISTING="$EXISTING  - Docker container: $POSTGRES_DOCKER_CONTAINER\n"
    fi
}

prompt_cleanup() {
    warn "Existing test environment found:"
    echo -e "$EXISTING"
    read -p "Clean up and continue? (y/N) " -n 1 -r
    echo
    if [ "$REPLY" != "y" ] && [ "$REPLY" != "Y" ]; then
        error "Tests require a clean environment."
        error_exit "Run './run.sh clean' to remove existing containers, or answer 'y' to clean automatically."
    fi
}

do_cleanup() {
    info "Cleaning up existing environment..."
    "$SCRIPT_DIR/../cleanup/teardown.sh"
}

check_existing

if [ -n "$EXISTING" ]; then
    prompt_cleanup
    do_cleanup
fi
