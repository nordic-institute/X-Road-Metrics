#!/bin/bash
# Run E2E test scenarios

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config/env.sh"
source "$SCRIPT_DIR/scripts/helpers/common.sh"

#-----------------------------------------------------------------------------
# Usage
#-----------------------------------------------------------------------------

usage() {
    info "Usage: $0 <command> [options]"
    echo ""
    info "Commands:"
    info "  build [modules...]     Build packages for jammy and noble"
    info "  test-jammy-latest-dbs  Fresh install on Jammy + latest DBs (Mongo 8, PG 18)"
    info "  test-noble-latest-dbs  Fresh install on Noble + latest DBs (Mongo 8, PG 18)"
    info "  test-noble-old-dbs     Fresh install on Noble + old DBs (Mongo 6, PG 14)"
    info "  test-upgrade           Upgrade test: old packages + old DBs -> new packages"
    info "  clean                  Remove test containers (LXD and Docker)"
    echo ""
    info "Options:"
    info "  --real-xroad     Use real X-Road servers instead of WireMock"
    info "  --always-keep    Keep LXD and Docker containers regardless of test outcome"
    info "  --always-clean   Remove LXD and Docker containers regardless of test outcome"
    echo ""
    info "Default: On success, LXD and Docker containers are removed. On failure, containers are kept for debugging."
    exit 1
}

#-----------------------------------------------------------------------------
# Parse arguments
#-----------------------------------------------------------------------------

export XROAD_MODE="mock"
CLEANUP_MODE="default"  # default | always-keep | always-clean
XROAD_MODE_LABEL=""
COMMAND=""
EXTRA_ARGS=""

for arg in "$@"; do
    case "$arg" in
        --real-xroad)
            export XROAD_MODE="real"
            XROAD_MODE_LABEL="(real-xroad)"
            ;;
        --always-keep)
            CLEANUP_MODE="always-keep"
            ;;
        --always-clean)
            CLEANUP_MODE="always-clean"
            ;;
        -*)
            error "Unknown option: $arg"
            echo ""
            usage
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="$arg"
            else
                # Collect extra positional args (e.g., module names for build)
                EXTRA_ARGS="$EXTRA_ARGS $arg"
            fi
            ;;
    esac
done

if [ -z "$COMMAND" ]; then
    usage
fi

#-----------------------------------------------------------------------------
# Dependency helpers
#-----------------------------------------------------------------------------

# All available modules
PACKAGES=(
    xroad-metrics-collector
    xroad-metrics-corrector
    xroad-metrics-anonymizer
    xroad-metrics-opendata-collector
    xroad-metrics-reports
    xroad-metrics-opendata
    xroad-metrics-networking
)

# Verify all expected packages exist for a distro
ensure_packages_built() {
    local distro="$1"
    local pkg_dir="$PACKAGES_DIR/$distro"

    for pkg in "${PACKAGES[@]}"; do
        ls "$pkg_dir"/${pkg}_*.deb >/dev/null 2>&1 || {
            error_exit "Missing $pkg in $pkg_dir — run './run.sh build' first"
        }
    done
}

#-----------------------------------------------------------------------------
# Cleanup handler
#-----------------------------------------------------------------------------

do_cleanup() {
    "$HELPERS_DIR/cleanup/teardown.sh" || true
}

handle_result() {
    local exit_code=$1

    if [ $exit_code -eq 0 ]; then
        # Success
        case "$CLEANUP_MODE" in
            always-keep)
                info "Containers kept (--always-keep)."
                print_container_access_hint
                ;;
            always-clean|default)
                do_cleanup
                ;;
        esac
    else
        # Failure
        case "$CLEANUP_MODE" in
            always-clean)
                do_cleanup
                ;;
            always-keep|default)
                warn "Containers kept for debugging."
                print_container_access_hint
                ;;
        esac
    fi
}

print_container_access_hint() {
    if [ -n "$DISTRO" ]; then
        local container_name="${CONTAINER_PREFIX}-${DISTRO}"
        local container_ip
        container_ip=$(lxc list "$container_name" --format csv -c 4 2>/dev/null | cut -d' ' -f1)

        info "LXD container: lxc exec $container_name -- bash"
        if [ -n "$container_ip" ]; then
            info "OpenData:      https://$container_ip/ (self-signed cert)"
            info "Networking:    http://$container_ip:3838/"
        fi
        info "Cleanup:       ./run.sh clean"
    fi
}

#-----------------------------------------------------------------------------
# Command mapping
#-----------------------------------------------------------------------------

DISTRO=""

case "$COMMAND" in
    build)
        SCENARIO_FILE="$SCENARIOS_DIR/build.sh"
        SCENARIO_ARGS="$EXTRA_ARGS"
        ;;
    test-jammy-latest-dbs)
        SCENARIO_FILE="$SCENARIOS_DIR/fresh-install.sh"
        SCENARIO_ARGS="jammy latest-dbs"
        DISTRO="jammy"
        ensure_packages_built jammy
        ;;
    test-noble-latest-dbs)
        SCENARIO_FILE="$SCENARIOS_DIR/fresh-install.sh"
        SCENARIO_ARGS="noble latest-dbs"
        DISTRO="noble"
        ensure_packages_built noble
        ;;
    test-noble-old-dbs)
        SCENARIO_FILE="$SCENARIOS_DIR/fresh-install.sh"
        SCENARIO_ARGS="noble old-dbs"
        DISTRO="noble"
        ensure_packages_built noble
        ;;
    test-upgrade)
        SCENARIO_FILE="$SCENARIOS_DIR/upgrade.sh"
        SCENARIO_ARGS="jammy old-dbs"
        DISTRO="jammy"
        ensure_packages_built jammy
        ;;
    clean)
        info "=== Cleaning up test containers ==="
        do_cleanup
        success "=== Cleanup complete ==="
        exit 0
        ;;
    *)
        error "Unknown command '$COMMAND'"
        echo ""
        usage
        ;;
esac

if [ ! -f "$SCENARIO_FILE" ]; then
    error_exit "Scenario file not found: $SCENARIO_FILE"
fi

#-----------------------------------------------------------------------------
# Run scenario
#-----------------------------------------------------------------------------

info "=== Running: $COMMAND ==="
echo ""

EXIT_CODE=0
if "$SCENARIO_FILE" ${SCENARIO_ARGS:-}; then
    echo ""
    success "=== PASSED: $COMMAND ${SCENARIO_ARGS:-} $XROAD_MODE_LABEL ==="
else
    EXIT_CODE=$?
    echo ""
    error "=== FAILED: $COMMAND ${SCENARIO_ARGS:-} $XROAD_MODE_LABEL ==="
fi

handle_result $EXIT_CODE
exit $EXIT_CODE
