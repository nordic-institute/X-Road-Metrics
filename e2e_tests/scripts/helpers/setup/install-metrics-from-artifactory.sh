#!/bin/bash
# Install xroad-metrics packages from Artifactory (for baseline testing)
#
# Usage: install-metrics-from-artifactory.sh <container-name>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

CONTAINER_NAME="${1:?Container name required}"

success "=== Installing packages from Artifactory in $CONTAINER_NAME ==="
info "Repository: $OLD_PACKAGES_URL"

lxc exec "$CONTAINER_NAME" -- bash -c "
    set -e

    # Add X-Road Extensions repository
    wget -qO - https://artifactory.niis.org/api/gpg/key/public | apt-key add -
    add-apt-repository -y 'https://artifactory.niis.org/xroad-extensions-release-deb main'

    apt-get update

    # Install all xroad-metrics packages
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        xroad-metrics-collector \
        xroad-metrics-corrector \
        xroad-metrics-anonymizer \
        xroad-metrics-opendata \
        xroad-metrics-reports \
        xroad-metrics-networking

    # Verify installation
    echo ''
    echo 'Installed packages:'
    apt list --installed 2>/dev/null | grep xroad-metrics || true
"

info "Installing Shiny Server (for networking module)..."
lxc exec "$CONTAINER_NAME" -- /usr/share/xroad-metrics/networking/install-shiny-server.sh --non-interactive

echo ""
success "=== Packages installed from Artifactory ==="
