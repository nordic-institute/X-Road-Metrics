#!/bin/bash

# Ensure required system dependencies are installed
sudo apt-get update && sudo apt-get install -y libpq-dev

# Install tox for running tests
pip install tox

# Install Python dependencies for all modules
modules=(
  "analysis_module"
  "analysis_ui_module"
  "anonymizer_module"
  "collector_module"
  "corrector_module"
  "opendata_collector_module"
  "opendata_module"
)

for module in "${modules[@]}"; do
  if [ -f "$module/requirements.txt" ]; then
    echo "Installing requirements for $module..."
    cd "$module" || exit
    pip install -r requirements.txt
    cd - || exit
  else
    echo "No requirements.txt found for $module, skipping."
  fi
done