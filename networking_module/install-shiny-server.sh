#!/bin/bash

SHINY_VERSION=1.5.16.958
PACKAGE_SHA=330e4e1c11251a2bd362de39063efaa3dbc87a6b06eced8472522147ad276ee4
PACKAGE_NAME=shiny-server-${SHINY_VERSION}-amd64.deb
TMP_DIR=/tmp/opmon/networking/shiny-server-install
INSTALLED_SHINY_VERSION=$(apt-cache policy shiny-server | grep Installed)

confirm_version_change() {
    echo "Another shiny-server version is already installed:"
    echo "shiny-server ${INSTALLED_SHINY_VERSION}"
    read -p "Replace the installed version with shiny-server ${SHINY_VERSION}? (y/N)" -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]];
    then
      echo "Aborted by user."
      exit 0
    fi
}

check_previous_installation() {
  if [[ "${INSTALLED_SHINY_VERSION}" == *${SHINY_VERSION}* ]];
  then
    echo "shiny-server ${SHINY_VERSION} already installed."
    exit 0
  elif \
    [[ "${INSTALLED_SHINY_VERSION}" == *Installed* ]] && \
    [[ ! "${INSTALLED_SHINY_VERSION}" == *none* ]];
  then
    confirm_version_change
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
  mkdir --parent ${TMP_DIR}
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
