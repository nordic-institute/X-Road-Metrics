#!/bin/bash

if [ "$#" -ne 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: ${0}"
    exit 1 || return 1
fi

# I'm currently here
CWD=$(pwd)
# Script to be executed is from ${APPDIR} ... go there!
DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${DIR}
# Name of subdirectory (under CLEAN_DATA_ARCHIVE_DIR/) where to move archive file
SUBDIR=$(/bin/date '+%Y/%m/%d')
# echo "SUBDIR = ${SUBDIR}"

# Settings is available at ${DIR}/settings.py
if ! [ -f ./settings.py ]; then
    echo "ERROR: Settings file ${DIR}/settings.py does not exist! Exiting ..."
    exit 1 || return 1
fi

# All settings in current bash script can be hardcoded, or calculated in bash level, commented out
# It is suggested to get settings through special python script
#
# MODULE="archiver"
# MODULE=$(grep "^MODULE = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MODULE=$(python3 ./get_settings.py MODULE)
# echo "MODULE = ${MODULE}"

# APPDIR="/opt/archive"
# APPDIR=$(grep "^APPDIR = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
APPDIR=$(python3 ./get_settings.py APPDIR)
# echo "APPDIR = ${APPDIR}"

# INSTANCES="XTEE-CI-XM ee-dev ee-test EE"
# INSTANCE="sample"
# INSTANCE=$(grep "^INSTANCE = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
INSTANCE=$(python3 ./get_settings.py INSTANCE)
# echo "INSTANCE = ${INSTANCE}"

# MONGODB_SERVER="127.0.0.1"
# MONGODB_SERVER="opmon.ci.kit"
# MONGODB_SERVER=$(grep "^MONGODB_SERVER = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MONGODB_SERVER=$(python3 ./get_settings.py MONGODB_SERVER)
# echo "MONGODB_SERVER = ${MONGODB_SERVER}"

# MONGODB_PORT="27017"
# MONGODB_PORT=$(grep "^MONGODB_PORT = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MONGODB_PORT=$(python3 ./get_settings.py MONGODB_PORT)
# echo "MONGODB_PORT = ${MONGODB_PORT}"

# MONGODB_USER="archiver_sample"
# MONGODB_USER="${MODULE}_${INSTANCE}"
# MONGODB_USER=$(grep "^MONGODB_USER = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MONGODB_USER=$(python3 ./get_settings.py MONGODB_USER)
# echo "MONGODB_USER = ${MONGODB_USER}"

# MONGODB_PWD=""
# MONGODB_PWD=$(grep "^MONGODB_PWD = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MONGODB_PWD=$(python3 ./get_settings.py MONGODB_PWD)
# echo "MONGODB_PWD = ${MONGODB_PWD}"

# MONGODB_QUERY_DB="query_db_sample"
# MONGODB_QUERY_DB="query_db_${INSTANCE}"
# MONGODB_QUERY_DB=$(grep "^MONGODB_QUERY_DB = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MONGODB_QUERY_DB=$(python3 ./get_settings.py MONGODB_QUERY_DB)
# echo "MONGODB_QUERY_DB = ${MONGODB_QUERY_DB}"

# MONGODB_AUTH_DB="auth_db" # or MONGODB_AUTH_DB="admin"
# MONGODB_AUTH_DB=$(grep "^MONGODB_AUTH_DB = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MONGODB_AUTH_DB=$(python3 ./get_settings.py MONGODB_AUTH_DB)
# echo "MONGODB_AUTH_DB = ${MONGODB_AUTH_DB}"

# MINIMUM_TO_ARCHIVE=100000
# MINIMUM_TO_ARCHIVE=$(grep "^MINIMUM_TO_ARCHIVE = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
MINIMUM_TO_ARCHIVE=$(python3 ./get_settings.py MINIMUM_TO_ARCHIVE)
# echo "MINIMUM_TO_ARCHIVE = ${MINIMUM_TO_ARCHIVE}"

# TOTAL_TO_ARCHIVE=150000
# TOTAL_TO_ARCHIVE=$(grep "^TOTAL_TO_ARCHIVE = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
TOTAL_TO_ARCHIVE=$(python3 ./get_settings.py TOTAL_TO_ARCHIVE)
# echo "TOTAL_TO_ARCHIVE = ${TOTAL_TO_ARCHIVE}"

# We do not need RAW_MESSAGES_ARCHIVE_DIR within this script
# RAW_MESSAGES_ARCHIVE_DIR="/srv/archive/sample"
# RAW_MESSAGES_ARCHIVE_DIR="/srv/archive/${INSTANCE}"
# RAW_MESSAGES_ARCHIVE_DIR=$(grep "^RAW_MESSAGES_ARCHIVE_DIR = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
# RAW_MESSAGES_ARCHIVE_DIR=$(python3 ./get_settings.py RAW_MESSAGES_ARCHIVE_DIR)
# echo "RAW_MESSAGES_ARCHIVE_DIR = ${RAW_MESSAGES_ARCHIVE_DIR}"

# CLEAN_DATA_ARCHIVE_DIR="/srv/archive/sample"
# CLEAN_DATA_ARCHIVE_DIR="/srv/archive/${INSTANCE}"
# CLEAN_DATA_ARCHIVE_DIR=$(grep "^CLEAN_DATA_ARCHIVE_DIR = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
CLEAN_DATA_ARCHIVE_DIR=$(python3 ./get_settings.py CLEAN_DATA_ARCHIVE_DIR)
# echo "CLEAN_DATA_ARCHIVE_DIR = ${CLEAN_DATA_ARCHIVE_DIR}"

# Prepare ${LOG} of current script
# Please note, that it depends of command ${0}
# Please note, that it is NOT the same as log for Python script
filename=$(basename -- "${0}")
extension="${filename##*.}"
filename="${filename%.*}"

# LOGGER_PATH="/opt/archive/sample/logs"
# LOGGER_PATH="${APPDIR}/${INSTANCE}/logs"
# LOGGER_PATH=$(grep "^LOGGER_PATH = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
LOGGER_PATH=$(python3 ./get_settings.py LOGGER_PATH)
# echo "LOGGER_PATH = ${LOGGER_PATH}"

# LOGGER_FILE="log_archiver_sample.json"
# LOGGER_FILE="log_${MODULE}_${INSTANCE}.json"
# LOGGER_FILE=$(grep "^LOGGER_FILE = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
LOGGER_FILE=$(python3 ./get_settings.py LOGGER_FILE)
# echo "LOGGER_FILE = ${LOGGER_FILE}"

# LOG=${LOGGER_PATH}/${LOGGER_FILE}
LOG="${APPDIR}/${INSTANCE}/logs/${filename}_${INSTANCE}.log"
# echo "LOG = ${LOG}"

# HEARTBEAT_PATH="/opt/archive/sample/heartbeat"
# HEARTBEAT_PATH="${APPDIR}/${INSTANCE}/heartbeat"
# HEARTBEAT_PATH=$(grep "^HEARTBEAT_PATH = " ./settings.py | tail -1 | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g" | sed -e "s/'//g")
HEARTBEAT_PATH=$(python3 ./get_settings.py HEARTBEAT_PATH)
# echo "HEARTBEAT_PATH = ${HEARTBEAT_PATH}"

# Prepare ${LOCK}
# Please note, that it depends of command ${0}
LOCK="${HEARTBEAT_PATH}/${filename}_${INSTANCE}.lock"
# echo "LOCK = ${LOCK}"

# Begin
PID=$$
echo -e "$(date +'%FT%T')\t${PID}: ${0} Start of archiving ${INSTANCE}" | tee -a ${LOG}
# Should be the same as `cd ${DIR}`
cd ${APPDIR}/${INSTANCE}/${MODULE}

# Dealing with ${LOCK}
if [ -f ${LOCK} ]; then
    echo -e "$(date +'%FT%T')\t${PID}: ${0} Warning: Lock file ${LOCK} exists! PID = $(cat ${LOCK}) -- Exiting!" | tee -a ${LOG}
    exit 1 || return 1
else
    # Create it
    echo "${PID}" > ${LOCK}
fi

# Actual stuff
python3 -u ./clean_data_archive.py \
    ${MONGODB_QUERY_DB} \
    ${MONGODB_USER} \
    --password ${MONGODB_PWD} \
    --auth ${MONGODB_AUTH_DB} \
    --host ${MONGODB_SERVER}:${MONGODB_PORT} \
    --total ${TOTAL_TO_ARCHIVE} \
    --minimum ${MINIMUM_TO_ARCHIVE} \
    --confirm True \
    2>&1 | tee -a ${LOG}

# Result of script should be available at ${CLEAN_DATA_ARCHIVE_DIR}
# Move archive to ${SUBDIR}
echo -e "$(date +'%FT%T')\t${PID}: ${0} Move archive to ${CLEAN_DATA_ARCHIVE_DIR}/${SUBDIR}/"  | tee -a ${LOG}
for file in $(find ${CLEAN_DATA_ARCHIVE_DIR}/clean_archive_query_db_${INSTANCE}_*.json.gz -newer ${LOCK}); do echo "=== ${file} ==="; SUBDIR=$(date -d "@$(stat -c '%Y' ${file})" '+%Y/%m/%d'); mkdir -p ${CLEAN_DATA_ARCHIVE_DIR}/${SUBDIR}; mv ${file} ${CLEAN_DATA_ARCHIVE_DIR}/${SUBDIR}; done 2>&1 | tee -a ${LOG}

# Remove ${LOCK}
/bin/rm ${LOCK} 2>&1 | tee -a ${LOG}

# The End
# df ${CLEAN_DATA_ARCHIVE_DIR} | tee -a ${LOG}
echo "${PID}: ${0} End of archiving ${INSTANCE}" | tee -a ${LOG}

# Go back to initial directory
cd ${CWD}
