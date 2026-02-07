#!/bin/bash
# Install xroad-metrics .deb packages in an LXD container
#
# Usage: install-metrics.sh <container-name> <distro>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

CONTAINER_NAME="${1:?Container name required}"
DISTRO="${2:?Distro required (jammy or noble)}"
PACKAGE_DIR="$PACKAGES_DIR/$DISTRO"

copy_packages_to_container() {
    lxc exec "$CONTAINER_NAME" -- mkdir -p /tmp/packages
    info "Copying packages to container..."
    for deb in "$PACKAGE_DIR"/*.deb; do
        info "  - $(basename "$deb")"
        lxc file push "$deb" "$CONTAINER_NAME/tmp/packages/"
    done
}

install_packages() {
    info "Installing packages..."
    lxc exec "$CONTAINER_NAME" -- bash -c '
        set -e
        cd /tmp/packages
        DEBIAN_FRONTEND=noninteractive apt-get install -y ./*.deb
        echo ""
        echo "Installed packages:"
        apt list --installed 2>/dev/null | grep xroad-metrics || true
    '
    lxc exec "$CONTAINER_NAME" -- rm -rf /tmp/packages
}

install_shiny_server() {
    info "Installing Shiny Server (for networking module)..."
    lxc exec "$CONTAINER_NAME" -- /usr/share/xroad-metrics/networking/install-shiny-server.sh --non-interactive
}

success "=== Installing packages in $CONTAINER_NAME ==="

copy_packages_to_container
install_packages
install_shiny_server

success "=== Packages installed successfully ==="
