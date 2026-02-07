#!/bin/bash
# X-Road Metrics E2E Test Environment Configuration

#-----------------------------------------------------------------------------
# Directory paths (derived from this file's location)
#-----------------------------------------------------------------------------
E2E_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR="$(cd "$E2E_DIR/.." && pwd)"
BUILD_DIR="$ROOT_DIR/output"
PACKAGES_DIR="$BUILD_DIR/artifacts"
SCENARIOS_DIR="$E2E_DIR/scripts/scenarios"
HELPERS_DIR="$E2E_DIR/scripts/helpers"
DOCKER_DIR="$E2E_DIR/docker"

#-----------------------------------------------------------------------------
# Container configuration
#-----------------------------------------------------------------------------
CONTAINER_PREFIX="xroad-metrics-e2e"

# LXD image names
LXD_IMAGE_JAMMY="ubuntu:22.04"
LXD_IMAGE_NOBLE="ubuntu:24.04"

#-----------------------------------------------------------------------------
# Database configuration
#-----------------------------------------------------------------------------
# MongoDB
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_LATEST_VERSION="8"
MONGO_OLD_VERSION="6"
MONGO_ADMIN_USER="admin"
MONGO_ADMIN_PASSWORD="e2e_test_password"

# PostgreSQL
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_LATEST_VERSION="18"
POSTGRES_OLD_VERSION="14"
PG_ADMIN_USER="postgres"
PG_ADMIN_PASSWORD="e2e_test_password"

#-----------------------------------------------------------------------------
# X-Road configuration
#-----------------------------------------------------------------------------
XROAD_INSTANCE="${XROAD_INSTANCE:-DEV}"
# Lowercase version for PostgreSQL naming (DEV -> dev, MY-INSTANCE -> my_instance)
XROAD_INSTANCE_LOWER=$(echo "$XROAD_INSTANCE" | tr '[:upper:]' '[:lower:]' | tr '-' '_')
# PostgreSQL database name (used by anonymizer, opendata, networking)
PG_DATABASE="opendata_${XROAD_INSTANCE_LOWER}"

# Set these when using real-xroad mode (ignored in mock mode)
CENTRAL_SERVER_HOST="${CENTRAL_SERVER_HOST:-}"
CENTRAL_SERVER_PORT="${CENTRAL_SERVER_PORT:-80}"
SECURITY_SERVER_HOST="${SECURITY_SERVER_HOST:-}"
SECURITY_SERVER_PORT="${SECURITY_SERVER_PORT:-80}"

#-----------------------------------------------------------------------------
# Artifactory configuration (for old packages)
#-----------------------------------------------------------------------------
OLD_PACKAGES_URL="https://artifactory.niis.org/xroad-extensions-release-deb"

#-----------------------------------------------------------------------------
# Docker container names (must match docker-compose.dbs.yml)
#-----------------------------------------------------------------------------
MONGO_DOCKER_CONTAINER="xroad-metrics-e2e-mongodb"
POSTGRES_DOCKER_CONTAINER="xroad-metrics-e2e-postgres"

#-----------------------------------------------------------------------------
# Export all variables
#-----------------------------------------------------------------------------
# Directories
export E2E_DIR ROOT_DIR BUILD_DIR PACKAGES_DIR SCENARIOS_DIR HELPERS_DIR DOCKER_DIR

# LXD
export CONTAINER_PREFIX LXD_IMAGE_JAMMY LXD_IMAGE_NOBLE

# MongoDB
export MONGO_PORT MONGO_LATEST_VERSION MONGO_OLD_VERSION
export MONGO_ADMIN_USER MONGO_ADMIN_PASSWORD MONGO_DOCKER_CONTAINER

# PostgreSQL
export POSTGRES_PORT POSTGRES_LATEST_VERSION POSTGRES_OLD_VERSION
export PG_ADMIN_USER PG_ADMIN_PASSWORD PG_DATABASE POSTGRES_DOCKER_CONTAINER

# X-Road
export XROAD_INSTANCE XROAD_INSTANCE_LOWER
export CENTRAL_SERVER_HOST CENTRAL_SERVER_PORT SECURITY_SERVER_HOST SECURITY_SERVER_PORT

# Artifactory
export OLD_PACKAGES_URL
