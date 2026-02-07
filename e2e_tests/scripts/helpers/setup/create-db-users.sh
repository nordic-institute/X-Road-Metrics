#!/bin/bash
# Initialize MongoDB and PostgreSQL using the built-in xroad-metrics init scripts.
# Must run AFTER package installation (the scripts come from the .deb packages).
#
# Uses --dummy-passwords so credentials are predictable (password = username).
#
# Usage: create-db-users.sh <container-name>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

CONTAINER_NAME="${1:?Container name required}"

#-----------------------------------------------------------------------------
# Setup
#-----------------------------------------------------------------------------

setup_environment() {
    # Host IP reachable from LXD container (Docker DBs run on the same host)
    HOST_IP=$(ip -4 addr show lxdbr0 2>/dev/null | awk '/inet / {split($2,a,"/"); print a[1]; exit}' || echo "10.0.0.1")
}

#-----------------------------------------------------------------------------
# Database initialization functions
#-----------------------------------------------------------------------------

create_mongo_users() {
    info "--- MongoDB: creating standard users ---"
    # Creates: collector, corrector, anonymizer, reports, analyzer, analyzer_interface
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics \
        xroad-metrics-init-mongo "$XROAD_INSTANCE" \
        --host "$HOST_IP:$MONGO_PORT" \
        --user "$MONGO_ADMIN_USER" --password "$MONGO_ADMIN_PASSWORD" \
        --dummy-passwords

    echo ""
    info "--- MongoDB: creating opendata_collector user ---"
    # opendata_collector is excluded by default, needs explicit flag
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics \
        xroad-metrics-init-mongo "$XROAD_INSTANCE" \
        --host "$HOST_IP:$MONGO_PORT" \
        --user "$MONGO_ADMIN_USER" --password "$MONGO_ADMIN_PASSWORD" \
        --dummy-passwords --user-to-generate opendata_collector
}

create_postgres_users() {
    info "--- PostgreSQL: creating database and users ---"
    # Creates database opendata_<instance> and users: anonymizer, opendata, networking
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics \
        xroad-metrics-init-postgresql "$XROAD_INSTANCE" \
        --host "$HOST_IP:$POSTGRES_PORT" \
        --user "$PG_ADMIN_USER" --password "$PG_ADMIN_PASSWORD" \
        --dummy-passwords

    # Grant schema permissions (PG 15+ compatibility — not done by the init script)
    echo ""
    info "--- PostgreSQL: granting schema permissions (PG 15+ compatibility) ---"
    docker exec "$POSTGRES_DOCKER_CONTAINER" psql -U "$PG_ADMIN_USER" -d "$PG_DATABASE" -c \
        "GRANT CREATE, USAGE ON SCHEMA public TO anonymizer_${XROAD_INSTANCE_LOWER};"
}

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------

setup_environment

success "=== Initializing databases ==="
info "  MongoDB: $HOST_IP:$MONGO_PORT"
info "  PostgreSQL: $HOST_IP:$POSTGRES_PORT"
echo ""

create_mongo_users
echo ""
create_postgres_users

echo ""
success "=== Databases initialized ==="
