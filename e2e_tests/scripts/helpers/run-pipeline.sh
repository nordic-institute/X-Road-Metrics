#!/bin/bash
# Run the xroad-metrics pipeline: collector -> corrector -> reports -> anonymizer -> networking -> opendata
#
# Usage: run-pipeline.sh <container-name>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../config/env.sh"
source "$SCRIPT_DIR/common.sh"

CONTAINER_NAME="${1:?Container name required}"
CORRECTOR_HEARTBEAT_FILE="/var/log/xroad-metrics/corrector/heartbeat/heartbeat_corrector_${XROAD_INSTANCE}.json"
REPORTS_OUTPUT_DIR="/var/lib/xroad-metrics/reports"
NETWORKING_OUTPUT_DIR="/var/lib/xroad-metrics/networking"

#-----------------------------------------------------------------------------
# Helpers
#-----------------------------------------------------------------------------

get_heartbeat_status() {
    lxc exec "$CONTAINER_NAME" -- cat "$CORRECTOR_HEARTBEAT_FILE" 2>/dev/null \
        | sed -n 's/.*"status": *"\([^"]*\)".*/\1/p' || echo ""
}

mongo_count() {
    local collection="$1"
    docker exec "$MONGO_DOCKER_CONTAINER" mongosh --quiet \
        -u "$MONGO_ADMIN_USER" -p "$MONGO_ADMIN_PASSWORD" \
        --authenticationDatabase admin \
        "query_db_$XROAD_INSTANCE" \
        --eval "db.${collection}.countDocuments({})" 2>/dev/null || echo "0"
}

#-----------------------------------------------------------------------------
# Pipeline steps
#-----------------------------------------------------------------------------

run_collector() {
    echo ""
    info "--- Running collector ---"
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics xroad-metrics-collector update
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics xroad-metrics-collector collect

    COLLECTOR_COUNT=$(mongo_count raw_messages)
    info "Raw messages count: $COLLECTOR_COUNT"

    if [ "$COLLECTOR_COUNT" -eq 0 ]; then
        error "No raw messages collected!"
        return 1
    fi
}

run_corrector() {
    echo ""
    info "--- Running corrector ---"

    # Start corrector in background (it runs in an infinite loop)
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics xroad-metrics-correctord &

    # Poll for heartbeat file with SUCCEEDED status
    info "Waiting for corrector to process records..."
    for i in $(seq 1 45); do
        STATUS=$(get_heartbeat_status)
        if [ "$STATUS" = "SUCCEEDED" ]; then
            break
        fi
        sleep 2
    done

    if [ "$STATUS" != "SUCCEEDED" ]; then
        error "Corrector did not complete successfully (status: ${STATUS:-not found})"
        return 1
    fi

    CORRECTOR_COUNT=$(mongo_count clean_data)
    info "Clean data count: $CORRECTOR_COUNT"

    if [ "$CORRECTOR_COUNT" -eq 0 ]; then
        error "No clean data produced!"
        return 1
    fi
}

run_reports() {
    echo ""
    info "--- Running reports ---"

    # Use fixed date range to cover mock data
    local start_date="2026-01-01"
    local end_date
    end_date=$(date +%Y-%m-%d)

    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics \
        xroad-metrics-reports report --start-date "$start_date" --end-date "$end_date"

    # Count generated PDF files
    REPORTS_COUNT=$(lxc exec "$CONTAINER_NAME" -- find "$REPORTS_OUTPUT_DIR" -name "*.pdf" 2>/dev/null | wc -l || echo "0")
    info "Reports generated: $REPORTS_COUNT"

    if [ "$REPORTS_COUNT" -eq 0 ]; then
        error "No reports generated!"
        return 1
    fi

    # Verify CSV files contain actual data (more than just header line)
    local csv_with_data
    csv_with_data=$(lxc exec "$CONTAINER_NAME" -- bash -c "
        for csv in \$(find $REPORTS_OUTPUT_DIR -name '*.csv' 2>/dev/null); do
            lines=\$(wc -l < \"\$csv\")
            if [ \"\$lines\" -gt 1 ]; then
                echo \"\$csv\"
                exit 0
            fi
        done
        exit 1
    " 2>/dev/null) || true

    if [ -z "$csv_with_data" ]; then
        error "Reports generated but CSV files contain no data!"
        return 1
    fi
    info "Verified: CSV files contain data"
}

run_anonymizer() {
    echo ""
    info "--- Running anonymizer ---"
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics xroad-metrics-anonymizer

    ANONYMIZER_COUNT=$(docker exec "$POSTGRES_DOCKER_CONTAINER" psql -U "$PG_ADMIN_USER" -t -c \
        "SELECT COUNT(*) FROM logs;" "$PG_DATABASE" 2>/dev/null | tr -d ' ' || echo "0")
    info "PostgreSQL logs count: $ANONYMIZER_COUNT"

    if [ "$ANONYMIZER_COUNT" -eq 0 ]; then
        error "No anonymized data in PostgreSQL!"
        return 1
    fi
}

run_networking() {
    echo ""
    info "--- Running networking ---"
    lxc exec "$CONTAINER_NAME" --cwd /tmp -- sudo -u xroad-metrics xroad-metrics-networking

    # Verify RDS files were created
    local dat_file="$NETWORKING_OUTPUT_DIR/dat.rds"
    local dates_file="$NETWORKING_OUTPUT_DIR/dates.rds"

    if ! lxc exec "$CONTAINER_NAME" -- test -f "$dat_file" 2>/dev/null; then
        error "Networking data file not created: $dat_file"
        return 1
    fi

    if ! lxc exec "$CONTAINER_NAME" -- test -f "$dates_file" 2>/dev/null; then
        error "Networking dates file not created: $dates_file"
        return 1
    fi

    info "Networking data files created successfully"
}

check_opendata() {
    if ! lxc exec "$CONTAINER_NAME" -- which xroad-metrics-opendata &>/dev/null; then
        return 0
    fi

    echo ""
    info "--- Checking opendata service ---"
    lxc exec "$CONTAINER_NAME" -- systemctl start xroad-metrics-opendata || true
    sleep 2

    CONTAINER_IP=$(lxc list "$CONTAINER_NAME" --format csv -c 4 | cut -d' ' -f1)
    if curl -s --connect-timeout 5 "http://$CONTAINER_IP:8000" >/dev/null; then
        info "OpenData service is responding at http://$CONTAINER_IP:8000"
    else
        warn "OpenData service not responding"
    fi
}

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------

success "=== Running full cycle test in $CONTAINER_NAME ==="

COLLECTOR_COUNT=0
CORRECTOR_COUNT=0
REPORTS_COUNT=0
ANONYMIZER_COUNT=0

run_collector
run_corrector
run_reports
run_anonymizer
run_networking
check_opendata

echo ""
success "=== Full cycle test completed successfully ==="
info "Results:"
info "  - Raw messages: $COLLECTOR_COUNT"
info "  - Clean data: $CORRECTOR_COUNT"
info "  - Reports generated: $REPORTS_COUNT"
info "  - Anonymized records: $ANONYMIZER_COUNT"
