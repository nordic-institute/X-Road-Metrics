#!/bin/bash
# Shared helpers for E2E test scripts

# =============================================================================
# Logging
# =============================================================================

IS_COLOR_ENABLED=$(command -v tput >/dev/null && tput setaf 1 &>/dev/null && echo true || echo false)

if $IS_COLOR_ENABLED; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    CYAN=$(tput setaf 6)
    RESET=$(tput sgr0)
else
    RED="" GREEN="" YELLOW="" CYAN="" RESET=""
fi

error_exit() {
    echo "${RED}ERROR: $*${RESET}" 1>&2
    exit 1
}

error() {
    echo "${RED}ERROR: $*${RESET}" 1>&2
}

warn() {
    echo "${YELLOW}WARNING: $*${RESET}"
}

success() {
    echo "${GREEN}$*${RESET}"
}

info() {
    echo "${CYAN}$*${RESET}"
}
