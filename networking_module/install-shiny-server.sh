#!/bin/bash

SHINY_VERSION=1.5.16.958
PACKAGE_SHA=330e4e1c11251a2bd362de39063efaa3dbc87a6b06eced8472522147ad276ee4
PACKAGE_NAME=shiny-server-${SHINY_VERSION}-amd64.deb
TMP_DIR=$(mktemp --tmp  --directory "xroad-metrics-install-shiny-server-XXXXXXX")

confirm_version_change() {
    echo "Another shiny-server version is already installed:"
    echo "shiny-server ${1}"
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
  wget -P ${TMP_DIR} https://download3.rstudio.org/ubuntu-14.04/x86_64/${PACKAGE_NAME}

}

install_shiny_server_package() {
  gdebi ${TMP_DIR}/${PACKAGE_NAME}
  rm -rf ${TMP_DIR}
}

check_previous_installation
download_shiny_server_package
verify_checksum
install_shiny_server_package
