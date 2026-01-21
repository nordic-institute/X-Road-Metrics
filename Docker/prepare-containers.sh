#!/bin/bash
set -e

MODULES=(collector_module corrector_module anonymizer_module opendata_module opendata_collector_module reports_module networking_module)

# Networking base image not available for ARM. Limit networking_module to AMD64 only.
AMD64_ONLY_MODULES=(networking_module)

usage() {
  echo "Usage: $0 [module]"
  echo "If no module is specified, all containers will be built."
  echo "Available modules: ${MODULES[*]}"
}

build_module() {
  local module=$1
  local tag="xroad-metrics-${module//_/-}"
  local dockerfile="Docker/${module}/Dockerfile"
  local platform_flag=""
  if [ ! -f "$dockerfile" ]; then
    echo "Dockerfile for $module not found!"
    exit 1
  fi

  # Check if module requires amd64 platform
  for amd64_module in "${AMD64_ONLY_MODULES[@]}"; do
    if [ "$module" == "$amd64_module" ]; then
      platform_flag="--platform=linux/amd64"
      break
    fi
  done

  echo "Building $tag from $dockerfile ..."
  docker build $platform_flag -t "$tag" -f "$dockerfile" .
}

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  usage
  exit 0
fi

if [ -n "$1" ]; then
  found=0
  for m in "${MODULES[@]}"; do
    if [ "$1" == "$m" ]; then
      build_module "$m"
      found=1
      break
    fi
  done
  if [ $found -eq 0 ]; then
    echo "Unknown module: $1"
    usage
    exit 1
  fi
else
  for m in "${MODULES[@]}"; do
    build_module "$m"
  done
fi
