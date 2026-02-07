#!/bin/bash
# Save or verify data counts for upgrade testing
#
# Usage: data-counts.sh save <label>
#        data-counts.sh verify <label>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../config/env.sh"
source "$SCRIPT_DIR/common.sh"

ACTION="${1:-}"
LABEL="${2:-}"

if [ -z "$ACTION" ] || [ -z "$LABEL" ]; then
    echo "Usage: $0 save|verify <label>"
    exit 1
fi

COUNTS_FILE="$BUILD_DIR/${LABEL}-counts.json"

get_counts() {
    MONGO_RAW=$(docker exec "$MONGO_DOCKER_CONTAINER" mongosh --quiet \
        -u "$MONGO_ADMIN_USER" -p "$MONGO_ADMIN_PASSWORD" \
        --authenticationDatabase admin \
        "query_db_$XROAD_INSTANCE" \
        --eval "db.raw_messages.countDocuments({})" 2>/dev/null || echo "0")

    MONGO_CLEAN=$(docker exec "$MONGO_DOCKER_CONTAINER" mongosh --quiet \
        -u "$MONGO_ADMIN_USER" -p "$MONGO_ADMIN_PASSWORD" \
        --authenticationDatabase admin \
        "query_db_$XROAD_INSTANCE" \
        --eval "db.clean_data.countDocuments({})" 2>/dev/null || echo "0")

    PG_LOGS=$(docker exec "$POSTGRES_DOCKER_CONTAINER" psql -U "$PG_ADMIN_USER" -t -c \
        "SELECT COUNT(*) FROM logs;" "$PG_DATABASE" 2>/dev/null | tr -d ' ' || echo "0")
}

save_counts() {
    mkdir -p "$BUILD_DIR"
    get_counts
    cat > "$COUNTS_FILE" << EOF
{"raw_messages": $MONGO_RAW, "clean_data": $MONGO_CLEAN, "logs": $PG_LOGS}
EOF
    info "Saved counts to $COUNTS_FILE"
    info "  raw_messages: $MONGO_RAW, clean_data: $MONGO_CLEAN, logs: $PG_LOGS"
}

read_saved_counts() {
    if [ ! -f "$COUNTS_FILE" ]; then
        error_exit "Counts file not found: $COUNTS_FILE"
    fi
    SAVED_RAW=$(jq -r '.raw_messages' "$COUNTS_FILE")
    SAVED_CLEAN=$(jq -r '.clean_data' "$COUNTS_FILE")
    SAVED_LOGS=$(jq -r '.logs' "$COUNTS_FILE")
}

verify_counts() {
    info "Verifying counts against $LABEL..."
    FAILED=0

    if [ "$MONGO_RAW" -ge "$SAVED_RAW" ]; then
        success "  raw_messages: $MONGO_RAW >= $SAVED_RAW"
    else
        error "  raw_messages: $MONGO_RAW < $SAVED_RAW"
        FAILED=1
    fi

    if [ "$MONGO_CLEAN" -ge "$SAVED_CLEAN" ]; then
        success "  clean_data: $MONGO_CLEAN >= $SAVED_CLEAN"
    else
        error "  clean_data: $MONGO_CLEAN < $SAVED_CLEAN"
        FAILED=1
    fi

    if [ "$PG_LOGS" -ge "$SAVED_LOGS" ]; then
        success "  logs: $PG_LOGS >= $SAVED_LOGS"
    else
        error "  logs: $PG_LOGS < $SAVED_LOGS"
        FAILED=1
    fi

    if [ $FAILED -ne 0 ]; then
        error_exit "Data verification failed"
    fi

    rm -f "$COUNTS_FILE"
}

case "$ACTION" in
    save)
        save_counts
        ;;

    verify)
        read_saved_counts
        get_counts
        verify_counts
        ;;

    *)
        echo "Unknown action: $ACTION"
        echo "Usage: $0 save|verify <label>"
        exit 1
        ;;
esac
