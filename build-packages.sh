#!/bin/bash
set -e

# =============================================================================
# Build deb packages for X-Road Metrics modules
# =============================================================================

# Change to project root directory.
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
cd "$SCRIPT_DIR"

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

# Available target distributions
TARGETS=(
  jammy
  noble
)

# Default output directory
OUTPUT_DIR="./output"

# =============================================================================
# Loggers
# =============================================================================
IS_COLOR_ENABLED=$(command -v tput >/dev/null && tput setaf 1 &>/dev/null && echo true || echo false)

errorExit() {
  if $IS_COLOR_ENABLED; then
    echo "$(tput setaf 5)*** $*$(tput sgr0)" 1>&2
  else
    echo "*** $*" 1>&2
  fi
  exit 1
}

warn() {
  if $IS_COLOR_ENABLED; then
    echo "$(tput setaf 3)*** $*$(tput sgr0)"
  else
    echo "*** $*"
  fi
}

success() {
  if $IS_COLOR_ENABLED; then
    echo "$(tput setaf 2)*** $*$(tput sgr0)"
  else
    echo "*** $*"
  fi
}

info() {
  if $IS_COLOR_ENABLED; then
    echo "$(tput setaf 6)$*$(tput sgr0)"
  else
    echo "$*"
  fi
}

# =============================================================================
# Helpers
# =============================================================================
check_module_exists() {
  local module=$1
  for valid_module in "${MODULES[@]}"; do
    if [ "$module" = "$valid_module" ]; then
      return 0
    fi
  done
  return 1
}

check_target_exists() {
  local target=$1
  for valid_target in "${TARGETS[@]}"; do
    if [ "$target" = "$valid_target" ]; then
      return 0
    fi
  done
  return 1
}

# =============================================================================
# Build function
# =============================================================================
build_package() {
  local module=$1
  local target=$2
  local output=$3

  local dockerfile="Dockerfile_${target}"
  local artifact_path="/artifacts/${target}"

  if [ ! -f "$dockerfile" ]; then
    errorExit "Dockerfile not found: $dockerfile"
  fi

  success "Building deb package for ${module} targeting ${target}..."
  info "Output directory: ${output}${artifact_path}"

  # Create output directory if it doesn't exist
  mkdir -p "$output"

  docker buildx build \
    --build-arg MODULE_NAME="$module" \
    --build-arg OUTPUT_PATH="$artifact_path" \
    . \
    --target=artifacts \
    --output "type=local,dest=${output}" \
    -f "$dockerfile"

  success "Package built successfully for ${module} (${target})"
  info "Check ${output}${artifact_path} for the generated .deb file(s)"
}

build_packages() {
  local target=$1
  local output=$2
  shift 2
  local modules_to_build=("$@")

  for module in "${modules_to_build[@]}"; do
    build_package "$module" "$target" "$output"
  done

  success "Build complete!"
}

# =============================================================================
# Usage/help
# =============================================================================
usage() {
  echo "Usage: $0 [-t <target>] [-o <output_dir>] [module1 module2 ...]"
  echo ""
  echo "Build deb packages for X-Road Metrics modules."
  echo ""
  echo "Optional arguments:"
  echo "  -t, --target <target>       Target Ubuntu distribution (default: all targets)"
  echo "  -o, --output <output_dir>   Output directory (default: ./output)"
  echo "  -h, --help                  Show this help message"
  echo ""
  echo "Module arguments:"
  echo "  If no modules are specified, all modules will be built."
  echo "  You can specify one or more module names after the options."
  echo ""
  echo "Available modules:"
  for m in "${MODULES[@]}"; do
    echo "  - $m"
  done
  echo ""
  echo "Available targets:"
  for t in "${TARGETS[@]}"; do
    echo "  - $t"
  done
  echo ""
  echo "Examples:"
  echo "  $0                                             # Build all modules for all targets"
  echo "  $0 collector_module                            # Build collector_module for all targets"
  echo "  $0 -t jammy                                    # Build all modules for jammy"
  echo "  $0 -t jammy collector_module corrector_module  # Build specific modules for jammy"
  echo "  $0 --output ./packages                         # Build all modules with custom output"
}

# =============================================================================
# Parse arguments
# =============================================================================
TARGET=""
SELECTED_MODULES=()

while [ $# -gt 0 ]; do
  case "$1" in
    -t|--target)
      if [ -z "$2" ] || [ "${2#-}" != "$2" ]; then
        errorExit "Option $1 requires a target name"
      fi
      TARGET="$2"
      shift 2
      ;;
    -o|--output)
      if [ -z "$2" ] || [ "${2#-}" != "$2" ]; then
        errorExit "Option $1 requires an output directory"
      fi
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      errorExit "Unknown option: $1. Use -h or --help for usage."
      ;;
    *)
      # Positional argument - treat as module name
      SELECTED_MODULES+=("$1")
      shift
      ;;
  esac
done

# =============================================================================
# Validation
# =============================================================================
if [ -n "$TARGET" ] && ! check_target_exists "$TARGET"; then
  usage
  errorExit "Unknown target: $TARGET"
fi

# Validate module names if any were specified
for module in "${SELECTED_MODULES[@]}"; do
  if ! check_module_exists "$module"; then
    usage
    errorExit "Unknown module: $module"
  fi
done

# =============================================================================
# Main
# =============================================================================

# Determine which targets to build
if [ -z "$TARGET" ]; then
  SELECTED_TARGETS=("${TARGETS[@]}")
else
  SELECTED_TARGETS=("$TARGET")
fi

# Determine which modules to build
if [ ${#SELECTED_MODULES[@]} -eq 0 ]; then
  MODULES_TO_BUILD=("${MODULES[@]}")
else
  MODULES_TO_BUILD=("${SELECTED_MODULES[@]}")
fi

# Build packages for each target
for target in "${SELECTED_TARGETS[@]}"; do
  build_packages "$target" "$OUTPUT_DIR" "${MODULES_TO_BUILD[@]}"
done
