#!/usr/bin/env python3
"""Patch keys in a YAML settings file.

Usage: configure-settings.py <file> --key.path=value ...
"""

import json
import sys
import yaml

def convert(value):
    """Convert a string value to its appropriate Python type.

    Attempts conversion in order: bool, JSON (for lists/dicts), int, float.
    Returns the original string if no conversion succeeds.
    """
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value

filepath = sys.argv[1]
with open(filepath) as f:
    data = yaml.safe_load(f) or {}

for arg in sys.argv[2:]:
    key, value = arg.lstrip("-").split("=", 1)
    keys = key.split(".")
    node = data
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    node[keys[-1]] = convert(value)

with open(filepath, "w") as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Updated: {filepath}")
