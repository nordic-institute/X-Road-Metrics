#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

# --------------------------------------------------------
# General settings
# --------------------------------------------------------
MODULE = "collector"
APPDIR = "/srv/app"
# X-Road instances in Estonia: ee-dev, ee-test, EE
INSTANCE = "sample"

# --------------------------------------------------------
# MongoDB settings
# --------------------------------------------------------
MONGODB_USER = '{0}_{1}'.format(MODULE, INSTANCE)
MONGODB_PWD = ""
MONGODB_SERVER = ""
MONGODB_SUFFIX = '{0}'.format(INSTANCE)

# --------------------------------------------------------
# Module settings
# --------------------------------------------------------
# IP or URI of Instance Central Server
CENTRAL_SERVER = ""
# Timeout for CENTRAL_SERVER requests
CENTRAL_SERVER_TIMEOUT = 10

# IP or URL of Instance Security Server
SECURITY_SERVER_URL = ""
# Timeout for SERVER_URL http requests.
SECURITY_SERVER_TIMEOUT = 60.0

# Message header of Instance Monitoring Client
# MEMBERCLASS is in {GOV, COM, NGO, NEE}
# Sample: MEMBERCLASS = "GOV"
MEMBERCLASS = "GOV"
# MEMBERCODE is registry code of institution
# Sample: MEMBERCODE = "70006317" # RIA, Riigi Infosüsteemi Amet, Republic of Estonia, Information System Authority
MEMBERCODE = ""
# SUBSYSTEMCODE is X-Road subsystem code, to be registered in RIHA, www.riha.ee
# Sample: SUBSYSTEMCODE = "monitoring"
SUBSYSTEMCODE = ""
MONITORING_CLIENT = """        <xrd:client id:objectType="SUBSYSTEM">
            <id:xRoadInstance>{0}</id:xRoadInstance>
            <id:memberClass>{1}</id:memberClass>
            <id:memberCode>{2}</id:memberCode>
            <id:subsystemCode>{3}</id:subsystemCode>
        </xrd:client>
""".format(INSTANCE, MEMBERCLASS, MEMBERCODE, SUBSYSTEMCODE)

# Match THREAD_COUNT with number of cores * CPUs available to ensure best performance
THREAD_COUNT = 4

# Amount of history to ask in the first time (in seconds).
# 1 min = 60 sec
# 1h = 60 min = 3600 sec
# RECORDS_FROM_OFFSET = 3600
# 1 day = 24h = 86400 seconds
# RECORDS_FROM_OFFSET = 86400
# 1 week = 7 days = 604800 seconds
RECORDS_FROM_OFFSET = 604800

# Offset for the records_to parameter (gets records only up to "current time" - RECORDS_TO_OFFSET).
# Set this value to higher than default records-available-timestamp-offset-seconds=60
# Must be smaller than RECORDS_FROM_OFFSET
RECORDS_TO_OFFSET = 100

# Repeat query to fetch additional data only if server has returned at least as much records.
# By default servers should return 10000 records, so this value should be smaller.
REPEAT_MIN_RECORDS = 50

# How many times to repeat query if server has more records ("nextRecordsFrom" is returned by previous query).
# Set to 0 to disable query repeating.
# If this value is too low and script is executed rarely then some data may be lost.
REPEAT_LIMIT = 100

# --------------------------------------------------------
# Configure logger
# --------------------------------------------------------
# Ensure match with external logrotate settings
LOGGER_NAME = '{0}'.format(MODULE)
LOGGER_PATH = '{0}/{1}/logs/'.format(APPDIR, INSTANCE)
LOGGER_FILE = 'log_{0}_{1}.json'.format(MODULE, INSTANCE)
LOGGER_LEVEL = logging.DEBUG

# --------------------------------------------------------
# Configure heartbeat
# --------------------------------------------------------
# Ensure match with external application monitoring settings
HEARTBEAT_PATH = '{0}/{1}/heartbeat/'.format(APPDIR, INSTANCE)
HEARTBEAT_FILE = 'heartbeat_{0}_{1}.json'.format(MODULE, INSTANCE)

# --------------------------------------------------------
# End of settings
# --------------------------------------------------------
