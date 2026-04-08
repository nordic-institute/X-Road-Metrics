#!/bin/bash
# Provision an LXD container for E2E testing
#
# Usage: provision-lxd-container.sh <distro>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

DISTRO="${1:-noble}"
CONTAINER_NAME="${CONTAINER_PREFIX}-${DISTRO}"

select_image() {
    case "$DISTRO" in
        jammy) LXD_IMAGE="$LXD_IMAGE_JAMMY" ;;
        noble) LXD_IMAGE="$LXD_IMAGE_NOBLE" ;;
        *) error_exit "Unknown distro '$DISTRO'. Use 'jammy' or 'noble'." ;;
    esac
}

create_container() {
    info "Creating container from $LXD_IMAGE..."
    lxc launch "$LXD_IMAGE" "$CONTAINER_NAME"
}

wait_for_ready() {
    info "Waiting for container to be ready..."
    for i in $(seq 1 30); do
        if lxc exec "$CONTAINER_NAME" -- systemctl is-system-running --wait &>/dev/null; then
            break
        fi
        sleep 2
    done

    info "Waiting for cloud-init to complete..."
    lxc exec "$CONTAINER_NAME" -- cloud-init status --wait || true
}

install_dependencies() {
    info "Updating package lists..."
    lxc exec "$CONTAINER_NAME" -- apt-get update -qq

    info "Installing dependencies..."
    lxc exec "$CONTAINER_NAME" -- apt-get install -y -qq \
        curl wget gnupg ca-certificates apt-transport-https software-properties-common
}

print_summary() {
    CONTAINER_IP=$(lxc list "$CONTAINER_NAME" --format csv -c 4 | cut -d' ' -f1)
    echo ""
    success "=== Container provisioned successfully ==="
    info "Container: $CONTAINER_NAME"
    info "IP: $CONTAINER_IP"
    info "To access: lxc exec $CONTAINER_NAME -- bash"
}

success "=== Provisioning LXD container: $CONTAINER_NAME ==="

select_image
create_container
wait_for_ready
install_dependencies
print_summary
