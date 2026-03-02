#!/bin/bash

SHINY_VERSION=1.5.23.1030
PACKAGE_SHA=4a3d063a06ccd1b6c53eb1d7f4fb59965bced10d1c5c87e8c476b58dd6fd35ee
PACKAGE_NAME=shiny-server-${SHINY_VERSION}-amd64.deb

# Parse arguments
NON_INTERACTIVE=false
for arg in "$@"; do
    case "$arg" in
        --non-interactive)
            NON_INTERACTIVE=true
            ;;
    esac
done

confirm_version_change() {
    echo "Another shiny-server version is already installed:"
    echo "shiny-server ${1}"
    if [ "$NON_INTERACTIVE" = true ]; then
        echo "Non-interactive mode: proceeding with replacement."
        return
    fi
    read -p "Replace the installed version with shiny-server ${SHINY_VERSION}? (y/N)" -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]];
    then
      echo "Aborted by user."
      exit 0
    fi
}

exit_if_already_installed() {
  if [[ ${1} == *${SHINY_VERSION}* ]];
  then
    echo "shiny-server ${SHINY_VERSION} already installed."
    exit 0
  fi
}

check_previous_installation() {
  if [[ $(dpkg-query --showformat='${Status}' --show shiny-server) == *installed* ]];
  then
    local INSTALLED_SHINY_VERSION
    INSTALLED_SHINY_VERSION=$(dpkg-query --showformat='${Version}' --show shiny-server)
    exit_if_already_installed "$INSTALLED_SHINY_VERSION"
    confirm_version_change "$INSTALLED_SHINY_VERSION"
  fi
}

verify_checksum() {
    if ! echo "${PACKAGE_SHA} *${TMP_DIR}/${PACKAGE_NAME}" | shasum -a 256 -c;
    then
      echo "Checksum failed for package ${TMP_DIR}/${PACKAGE_NAME}. Aborting installation." >&2
      rm -rf ${TMP_DIR}
      exit 1
    fi
}

download_shiny_server_package() {
  TMP_DIR=$(mktemp --tmp  --directory "xroad-metrics-install-shiny-server-XXXXXXX")
  chmod 755 "$TMP_DIR"
  wget -P ${TMP_DIR} https://download3.rstudio.org/ubuntu-20.04/x86_64/${PACKAGE_NAME}
}

install_shiny_server_package() {
  if [ "$NON_INTERACTIVE" = true ]; then
    DEBIAN_FRONTEND=noninteractive apt-get install -y "${TMP_DIR}/${PACKAGE_NAME}"
  else
    apt install "${TMP_DIR}/${PACKAGE_NAME}"
  fi
  rm -rf "${TMP_DIR}"
}

check_previous_installation
download_shiny_server_package
verify_checksum
install_shiny_server_package
