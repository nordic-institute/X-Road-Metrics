#!/bin/bash
set -e

# Default to /app/etc/settings.yaml, but allow override
SETTINGS_FILE=${SETTINGS_FILE:-/app/etc/settings.yaml}

# Only update if settings file exists
if [ -f "$SETTINGS_FILE" ]; then
  # Loop through all environment variables
  env | while IFS='=' read -r VAR VALUE; do
    # Only process variables with at least one dot (.)
    if [[ "$VAR" == *.* ]]; then
      # Convert env var name to yq path (replace _ with - for YAML keys)
      YQ_PATH=$(echo "$VAR" | sed 's/_/-/g' | sed 's/\././g')
      # Use yq to set the value in the YAML file
      yq -i ".${YQ_PATH} = \"${VALUE}\"" "$SETTINGS_FILE"
    fi
  done
fi

exec "$@"
