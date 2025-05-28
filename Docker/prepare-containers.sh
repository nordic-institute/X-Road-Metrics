#!/bin/bash
set -e

MODULES=(collector_module corrector_module anonymizer_module opendata_module opendata_collector_module reports_module)

usage() {
  echo "Usage: $0 [module]"
  echo "If no module is specified, all containers will be built."
  echo "Available modules: ${MODULES[*]}"
}

build_module() {
  local module=$1
  local tag="xroad-metrics-${module//_/-}"
  local dockerfile="Docker/${module}/Dockerfile"
  if [ ! -f "$dockerfile" ]; then
    echo "Dockerfile for $module not found!"
    exit 1
  fi
  echo "Building $tag from $dockerfile ..."
  docker build -t "$tag" -f "$dockerfile" .
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
