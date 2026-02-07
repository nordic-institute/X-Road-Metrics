#!/bin/bash
# Start MongoDB and PostgreSQL Docker containers
#
# Usage: start-dbs.sh <db-versions>
#   db-versions: latest-dbs or old-dbs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../config/env.sh"
source "$SCRIPT_DIR/../common.sh"

DB_VERSIONS="${1:?Usage: $0 <db-versions> (latest-dbs or old-dbs)}"

# MONGO_VERSION and PG_VERSION are used by docker-compose.dbs.yml to select image tags
if [ "$DB_VERSIONS" = "old-dbs" ]; then
    export MONGO_VERSION=${MONGO_OLD_VERSION}
    export PG_VERSION=${POSTGRES_OLD_VERSION}
else
    export MONGO_VERSION=${MONGO_LATEST_VERSION}
    export PG_VERSION=${POSTGRES_LATEST_VERSION}
fi

info "Starting databases (Mongo ${MONGO_VERSION}, PG ${PG_VERSION})..."
docker compose -f "$DOCKER_DIR/docker-compose.dbs.yml" up -d --wait
