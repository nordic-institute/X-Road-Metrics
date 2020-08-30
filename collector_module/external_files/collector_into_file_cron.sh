#!/bin/bash

# Sample scripts to collect X-Road v6 operational monitoring data from security servers.
# Includes:
# collector_into_file_cron.sh - main script (bash) to be executed manually or from crontab. Sample: */15 * * * * /path/to/collector_into_file_cron.sh
# collector_into_file_list_servers.py - Python script to prepare list of security servers, from where operational monitoring data to be collected
# collector_into_file_get_opmon.py - Python script to collect operational monitoring data from given security server

#
# Variables
# 
# Executables
PYTHON="/usr/bin/python"
# Get current working directory
CWD=$(pwd)
LIST_SERVERS="${CWD}/collector_into_file_list_servers.py"
GET_OPMON="${CWD}/collector_into_file_get_opmon.py"

#
# IP or Name of Central Server
CENTRAL_SERVER="213.184.41.178"

# Current timestamp
NOW=$(/bin/date +"%Y-%m-%d_%H:%M:%S%z")
# A cache file is used when Central Server does not reply
CACHE_DIR="."
CACHE_EXT="txt"
SERVERS_CACHE_NOW="${CACHE_DIR}/cache_${CENTRAL_SERVER}_${NOW}.${CACHE_EXT}"
SERVERS_CACHE="${CACHE_DIR}/cache_${CENTRAL_SERVER}.${CACHE_EXT}"
# Directory to keep result files, log directory
LOG_DIR="."
LOG_EXT="log"
LOG_FILE="log_${CENTRAL_SERVER}_${NOW}.${LOG_EXT}"
STATUS="${LOG_DIR}/${0%.*}.${LOG_EXT}"

echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} started" >> ${STATUS}

#
# Basic checks before actual work
#
# We do expect Python available
if [ ! -x "${PYTHON}" ] || [ ! -f "${PYTHON}" ]
then
    echo "ERROR: ${PYTHON} is not executable or available!"
    echo "ERROR: ${PYTHON} is not executable or available!" >> ${STATUS}
    echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} exit 1" >> ${STATUS}
    exit 1
fi

# We do expect Python ver 2.x available
PYTHON_VERSION=$(${PYTHON} -V 2>&1)
if [[ "${PYHON_VERSION}" =~ "2." ]]
then
    echo "ERROR: ${PYTHON} version 2.x is required!"
    echo "ERROR: ${PYTHON} version 2.x is required!" >> ${STATUS}
    echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} exit 1" >> ${STATUS}
    exit 1
fi

# We do expect required Python scripts available
if [ ! -f "${LIST_SERVERS}" ]
then
    echo "ERROR: File ${LIST_SERVERS} does not exist!"
    echo "ERROR: File ${LIST_SERVERS} does not exist!" >> ${STATUS}
    echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} exit 1" >> ${STATUS}
    exit 1
fi

if [ ! -f "${GET_OPMON}" ]
then
    echo "ERROR: File ${GET_OPMON} does not exist!"
    echo "ERROR: File ${GET_OPMON} does not exist!" >> ${STATUS}
    echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} exit 1" >> ${STATUS}
    exit 1
fi

# We do expect working directory exists
if [ ! -d "${LOG_DIR}" ]
then
    echo "ERROR: Log directory ${LOG_DIR} does not exist!"
    echo "ERROR: Log directory ${LOG_DIR} does not exist!" >> ${STATUS}
    echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} exit 1" >> ${STATUS}
    exit 1
fi

#
# Do the actual stuff
#
# Receive list of security servers available from CENTRAL_SERVER global configuration
# When succeeded, keep it in cache file
# When failed, use cache file
DATA=$(${PYTHON} ${LIST_SERVERS} ${CENTRAL_SERVER})
EXIT_CODE=$?

if [ ${EXIT_CODE} -ne 0 ]; then
    echo "WARNING: command '${PYTHON} ${LIST_SERVERS} ${CENTRAL_SERVER}' exited with code ${EXIT_CODE}"
    echo "WARNING: command '${PYTHON} ${LIST_SERVERS} ${CENTRAL_SERVER}' exited with code ${EXIT_CODE}" >> ${STATUS}
fi

if [[ -z ${DATA} ]]; then
    DATA=$(/bin/cat ${SERVERS_CACHE})
    if [[ -z ${DATA} ]]; then
        echo "ERROR: Server list not available"
        echo "ERROR: Server list not available" >> ${STATUS}
        echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} exit 1" >> ${STATUS}
        exit 1
    fi
else
    echo "${DATA}" > ${SERVERS_CACHE_NOW}
        /bin/rm -f ${SERVERS_CACHE}
        /bin/ln -s ${SERVERS_CACHE_NOW} ${SERVERS_CACHE}
fi

# Receive operational monitoring data from security servers in list
# Script GET_OPMON keeps the status of data received in ${LOG_DIR}/nextRecordsFrom.json
cd ${LOG_DIR}/
echo "${DATA}" | ${PYTHON} -u ${GET_OPMON} > ${LOG_FILE} 2>&1
EXIT_CODE=$?
cd ${CWD}/
echo "$(/bin/date +"%Y-%m-%d_%H:%M:%S%z"): ${0} exit ${EXIT_CODE}" >> ${STATUS}
