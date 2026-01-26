#!/bin/bash
set -e

# Change to project root directory.
# Allows running by Docker/prepare-containers.sh or ./prepare-containers.sh
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
cd "$SCRIPT_DIR/.."

# =============================================================================
# Configuration
# =============================================================================

# All available modules
MODULES=(
  collector_module
  corrector_module
  anonymizer_module
  opendata_collector_module
  reports_module
  opendata_module
  networking_module
)

# Modules that require amd64 platform
AMD64_ONLY_MODULES=(networking_module)

get_base_image() {
  case "$1" in
    opendata_module)   echo "3.11-slim-bookworm" ;;
    networking_module) ;;
    *)                 echo "3.8-slim" ;;
  esac
}

# =============================================================================
# Loggers
# =============================================================================
IS_COLOR_ENABLED=$(command -v tput >/dev/null && tput setaf 1 &>/dev/null && echo true || echo false)

errorExit() {
  echo ""
  if $IS_COLOR_ENABLED; then
    echo "$(tput setaf 5)*** $*$(tput sgr0)" 1>&2
  else
    echo "*** $*" 1>&2
  fi
  exit 1
}

warn() {
  echo ""
  if $IS_COLOR_ENABLED; then
    echo "$(tput setaf 3)*** $*$(tput sgr0)"
  else
    echo "*** $*"
  fi
  echo ""
}

success() {
  echo ""
  if $IS_COLOR_ENABLED; then
    echo "$(tput setaf 2)*** $*$(tput sgr0)"
  else
    echo "*** $*"
  fi
  echo ""
}

# =============================================================================
# Helpers
# =============================================================================
check_module_exists() {
  local module=$1
  for valid_module in "${MODULES[@]}"; do
    if [ "$module" == "$valid_module" ]; then
      return 0
    fi
  done
  usage
  errorExit "Unknown module: $module"
}

get_required_base_versions() {
  REQUIRED_BASE_VERSIONS=()
  for module in "$@"; do
    local base_image=$(get_base_image "$module")
    if [[ -n "$base_image" ]]; then
      # Check if already in array (simple approach, fine for 2-3 versions)
      if [[ ! " ${REQUIRED_BASE_VERSIONS[*]} " =~ " ${base_image} " ]]; then
        REQUIRED_BASE_VERSIONS+=("$base_image")
      fi
    fi
  done
}

# =============================================================================
# Build functions
# =============================================================================
build_base_images() {
  get_required_base_versions "$@"

  if [[ ${#REQUIRED_BASE_VERSIONS[@]} -eq 0 ]]; then
    warn "No base images needed"
    return
  fi

  success "Building ${#REQUIRED_BASE_VERSIONS[@]} base image(s)..."

  for python_version in "${REQUIRED_BASE_VERSIONS[@]}"; do
    local tag="xroad-metrics-base:${python_version}"

    success "Building base image ${tag}..."
    docker build \
      --build-arg PYTHON_VERSION="${python_version}" \
      -t "${tag}" \
      -f Docker/metrics-base/Dockerfile \
      .
  done

  success "Base images built successfully"
}

build_module_image() {
  local module=$1
  local dockerfile="Docker/${module}/Dockerfile"
  local tag="xroad-metrics-${module//_/-}"

  if [[ ! -f "$dockerfile" ]]; then
    errorExit "Dockerfile not found: $dockerfile"
  fi

  local build_args=()

  for amd64_module in "${AMD64_ONLY_MODULES[@]}"; do
    if [ "$module" == "$amd64_module" ]; then
      build_args+=(--platform=linux/amd64)
      break
    fi
  done

  local base_image=$(get_base_image "$module")
  if [[ -n "$base_image" ]]; then
    build_args+=(--build-arg "BASE_IMAGE=xroad-metrics-base:${base_image}")
  fi

  success "Building ${tag}..."
  docker build "${build_args[@]}" -t "${tag}" -f "${dockerfile}" .
}

build_images() {
  local modules=("$@")

  build_base_images "${modules[@]}"

  for module in "${modules[@]}"; do
    build_module_image "$module"
  done

  success "Build complete!"
}

# =============================================================================
# Usage/help
# =============================================================================
usage() {
  echo "Usage: $0 [module1 module2 ...]"
  echo "  If no module is specified, all containers will be built."
  echo "  Available modules:"
  for m in "${MODULES[@]}"; do
    echo "    - $m"
  done
}

# =============================================================================
# Main
# =============================================================================
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
  usage
  exit 0
fi

# Validate module names before building anything
for module in "$@"; do
  check_module_exists "$module"
done

if [[ $# -eq 0 ]]; then
  # Building images of all modules
  build_images "${MODULES[@]}"
else
  # Building images of required modules only
  build_images "$@"
fi
