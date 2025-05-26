#!/bin/bash
set -e

# Default to /app/etc/settings.yaml, but allow override
METRICS_SETTINGS_FILE=${METRICS_SETTINGS_FILE:-/app/settings.yaml}

# Only update if settings file exists
if [ -f "$METRICS_SETTINGS_FILE" ]; then
  # Loop through all environment variables
  env | while IFS='=' read -r VAR VALUE; do
    # Only process variables with 'setting_' prefix
    if [[ "$VAR" == setting_* ]]; then
      # Strip the 'setting_' prefix for the YAML path
      PATH_VAR=${VAR#setting_}
      # Convert to yq path (replace _ with - for YAML keys)
      YQ_PATH=$(echo "$PATH_VAR" | sed 's/_/-/g')
      # Determine if the value should be quoted (if not a number, boolean, or null)
      if [[ "$VALUE" =~ ^([0-9]+(\.[0-9]+)?|true|false|null)$ ]]; then
        # No quotes for numbers, booleans, or null
        yq -i ".${YQ_PATH} = ${VALUE}" "$METRICS_SETTINGS_FILE"
      else
        # Quote for strings
        yq -i ".${YQ_PATH} = \"${VALUE}\"" "$METRICS_SETTINGS_FILE"
      fi
    fi
  done
fi

exec "$@"
