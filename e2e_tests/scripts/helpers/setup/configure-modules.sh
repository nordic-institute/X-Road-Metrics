#!/bin/bash
# Configure xroad-metrics modules in an LXD container
#
# Usage: configure-modules.sh <container-name>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

CONTAINER_NAME="${1:?Container name required}"

#-----------------------------------------------------------------------------
# Setup
#-----------------------------------------------------------------------------

setup_environment() {
    # Host IP reachable from LXD container (Docker and WireMock run on the same host)
    # Note: Using awk instead of grep -oP for bash 3.2 compatibility
    HOST_IP=$(ip -4 addr show lxdbr0 2>/dev/null | awk '/inet / {split($2,a,"/"); print a[1]; exit}' || echo "10.0.0.1")

    # X-Road server configuration
    if [ "${XROAD_MODE:-mock}" = "mock" ]; then
        info "Using mock X-Road servers (WireMock)..."
        # Ports must match docker-compose.mock-xroad.yml
        CENTRAL_SERVER_HOST="$HOST_IP"
        CENTRAL_SERVER_PORT="80"
        SECURITY_SERVER_HOST="$HOST_IP"
        SECURITY_SERVER_PORT="4210"
    else
        info "Using real X-Road servers..."
        # Get Docker container IPs directly (LXD can reach Docker's bridge network)
        CENTRAL_SERVER_HOST="${CENTRAL_SERVER_HOST:-$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' cs 2>/dev/null || echo "$HOST_IP")}"
        CENTRAL_SERVER_PORT="${CENTRAL_SERVER_PORT:-80}"
        SECURITY_SERVER_HOST="${SECURITY_SERVER_HOST:-$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ss0 2>/dev/null || echo "$HOST_IP")}"
        SECURITY_SERVER_PORT="${SECURITY_SERVER_PORT:-8080}"
    fi

    # Construct host strings
    if [ "$CENTRAL_SERVER_PORT" = "80" ]; then
        CS_HOST="$CENTRAL_SERVER_HOST"
    else
        CS_HOST="$CENTRAL_SERVER_HOST:$CENTRAL_SERVER_PORT"
    fi
    SS_HOST="$SECURITY_SERVER_HOST:$SECURITY_SERVER_PORT"
    MONGO_HOST="$HOST_IP:$MONGO_PORT"

}

setup_configure_script() {
    info "Pushing configuration script to container..."
    lxc file push "$SCRIPT_DIR/configure-settings.py" "$CONTAINER_NAME/tmp/configure-settings.py"
    lxc exec "$CONTAINER_NAME" -- chmod +x /tmp/configure-settings.py

    # Ensure PyYAML is installed in container
    lxc exec "$CONTAINER_NAME" -- pip3 install pyyaml -q 2>/dev/null || \
        lxc exec "$CONTAINER_NAME" -- apt-get install -y -qq python3-yaml
}

cleanup_configure_script() {
    info "Removing configuration script from container..."
    lxc exec "$CONTAINER_NAME" -- rm -f /tmp/configure-settings.py
}

#-----------------------------------------------------------------------------
# Module configuration functions
#-----------------------------------------------------------------------------

# Helper: configure a module if its settings file exists
configure_module() {
    local module="$1"
    local settings_file="/etc/xroad-metrics/$module/settings.yaml"
    shift

    if lxc exec "$CONTAINER_NAME" -- test -f "$settings_file" 2>/dev/null; then
        info "Configuring $module..."
        lxc exec "$CONTAINER_NAME" -- /tmp/configure-settings.py "$settings_file" "$@"
    fi
}

configure_collector() {
    configure_module collector \
        "--xroad.instance=$XROAD_INSTANCE" \
        "--xroad.central-server.host=$CS_HOST" \
        "--xroad.security-server.host=$SS_HOST" \
        "--xroad.monitoring-client.memberclass=COM" \
        "--xroad.monitoring-client.membercode=1234" \
        "--xroad.monitoring-client.subsystemcode=metrics" \
        "--collector.records-to-offset=0" \
        "--mongodb.host=$MONGO_HOST" \
        "--mongodb.user=collector_${XROAD_INSTANCE}" \
        "--mongodb.password=collector_${XROAD_INSTANCE}"
}

configure_corrector() {
    configure_module corrector \
        "--xroad.instance=$XROAD_INSTANCE" \
        "--corrector.wait-on-done=30" \
        "--corrector.wait-on-error=30" \
        "--mongodb.host=$MONGO_HOST" \
        "--mongodb.user=corrector_${XROAD_INSTANCE}" \
        "--mongodb.password=corrector_${XROAD_INSTANCE}"
}

configure_anonymizer() {
    configure_module anonymizer \
        "--xroad.instance=$XROAD_INSTANCE" \
        "--xroad.central-server.host=$CS_HOST" \
        "--mongodb.host=$MONGO_HOST" \
        "--mongodb.user=anonymizer_${XROAD_INSTANCE}" \
        "--mongodb.password=anonymizer_${XROAD_INSTANCE}" \
        "--postgres.host=$HOST_IP" \
        "--postgres.port=$POSTGRES_PORT" \
        "--postgres.user=anonymizer_${XROAD_INSTANCE_LOWER}" \
        "--postgres.password=anonymizer_${XROAD_INSTANCE_LOWER}" \
        "--postgres.database-name=$PG_DATABASE" \
        "--postgres.readonly-users=[\"opendata_${XROAD_INSTANCE_LOWER}\", \"networking_${XROAD_INSTANCE_LOWER}\"]"
}

configure_opendata() {
    configure_module opendata \
        "--xroad.instance=$XROAD_INSTANCE" \
        "--postgres.host=$HOST_IP" \
        "--postgres.port=$POSTGRES_PORT" \
        "--postgres.user=opendata_${XROAD_INSTANCE_LOWER}" \
        "--postgres.password=opendata_${XROAD_INSTANCE_LOWER}" \
        "--postgres.database-name=$PG_DATABASE" \
        "--opendata.delay-days=0" \
        "--django.secret-key=e2e-test-secret"
}

configure_reports() {
    configure_module reports \
        "--xroad.instance=$XROAD_INSTANCE" \
        "--mongodb.host=$MONGO_HOST" \
        "--mongodb.user=reports_${XROAD_INSTANCE}" \
        "--mongodb.password=reports_${XROAD_INSTANCE}" \
        "--reports.generate-csv=True"
}

configure_networking() {
    configure_module networking \
        "--xroad.instance=$XROAD_INSTANCE" \
        "--postgres.host=$HOST_IP" \
        "--postgres.port=$POSTGRES_PORT" \
        "--postgres.username=networking_${XROAD_INSTANCE_LOWER}" \
        "--postgres.password=networking_${XROAD_INSTANCE_LOWER}" \
        "--networking.buffer=0"
}

configure_apache() {
    # OpenData and Networking packages both install Apache VHosts with the same
    # ServerName on port 443, causing a conflict. Apache routes all requests to
    # the first VHost (networking) and OpenData never receives requests.
    #
    # Fix: Disable the networking Apache VHost. OpenData uses Apache/WSGI on
    # port 443. Networking uses Shiny Server directly on port 3838.
    info "Configuring Apache (resolving VHost conflict)..."
    lxc exec "$CONTAINER_NAME" -- bash -c "
        if [ -f /etc/apache2/sites-enabled/00-xroad-metrics-networking.conf ]; then
            a2dissite 00-xroad-metrics-networking >/dev/null 2>&1 || true
        fi
        # Ensure Apache is running (packages may not start it automatically)
        if systemctl is-active --quiet apache2; then
            systemctl reload apache2
        else
            systemctl start apache2
        fi
    "
}

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------

success "=== Configuring xroad-metrics modules in $CONTAINER_NAME ==="

setup_environment

info "Configuration:"
info "  MongoDB: $MONGO_HOST"
info "  PostgreSQL: $HOST_IP:$POSTGRES_PORT"
info "  Central Server: $CS_HOST"
info "  Security Server: $SS_HOST"
info "  X-Road Instance: $XROAD_INSTANCE"
echo ""

setup_configure_script

configure_collector
configure_corrector
configure_anonymizer
configure_opendata
configure_reports
configure_networking
configure_apache

cleanup_configure_script

echo ""
success "=== Modules configured successfully ==="
