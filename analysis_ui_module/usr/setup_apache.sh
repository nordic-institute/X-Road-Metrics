#!/bin/bash

OPMON_DOC_ROOT="/var/www/opmon-analyzer-ui"

set -x

# Install Apache and mod-wsgi
apt update
apt install sudo libexpat1 apache2 apache2-utils ssl-cert libapache2-mod-wsgi-py3

# www-data user needs access to opmon app
usermod -a -G opmon www-data

# Prepare document root directory:
mkdir --parent ${OPMON_DOC_ROOT}/database
cp ./wsgi.py ${OPMON_DOC_ROOT}/

chown --recursive www-data:www-data ${OPMON_DOC_ROOT} && \
chmod --recursive -x+X ${OPMON_DOC_ROOT}

# Django setup:
sudo --user www-data  python3 ./manage.py makemigrations
sudo --user www-data  python3 ./manage.py migrate
sudo --user www-data  python3 ./manage.py collectstatic --no-input

# Start serving opmon-analyzer-ui
mod_wsgi-express install-module | head --lines 1 > /etc/apache2/mods-available/wsgi.load
a2ensite opmon-analyzer-ui.conf
apachectl start
