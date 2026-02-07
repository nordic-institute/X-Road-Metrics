#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../config/env.sh"
source "$SCRIPT_DIR/../helpers/common.sh"

# Module arguments (if any) are passed through
MODULES="$*"

# Clean old artifacts to avoid version conflicts
rm -rf "$PACKAGES_DIR"

info "Building jammy packages..."
"$ROOT_DIR/build-packages.sh" -t jammy -o "$BUILD_DIR" $MODULES

info "Building noble packages..."
"$ROOT_DIR/build-packages.sh" -t noble -o "$BUILD_DIR" $MODULES

echo ""
info "Verifying packages with lintian..."
for distro in jammy noble; do
    pkg_dir="$PACKAGES_DIR/$distro"
    if [ -d "$pkg_dir" ]; then
        for deb in "$pkg_dir"/*.deb; do
            if [ -f "$deb" ]; then
                info "Checking $deb..."
                lintian --fail-on error "$deb"
            fi
        done
    fi
done

success "All packages passed lintian verification."
