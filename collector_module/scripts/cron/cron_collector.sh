#!/bin/bash
#
# Part of X-Road v6 Operational Monitoring, https://github.com/ria-ee/X-Road-opmonitor
# Run ${0}
# From command line or from crontab
# Actual stuff is marked below
#
# All the rest is about logging command stdout and stderr into screen and into ${LOG}
#   and dealing with ${LOCK}
#
# Author: Toomas Mölder <toomas.molder@ria.ee>, skype: toomas.molder, phone: +372 5522000

# Prepare running environment
CWD=$(pwd)
dirname=$(dirname ${0})
cd ${dirname}

if [[ $# -eq 0 ]] ; then
    echo 'Usage: cron_collector.sh XROAD_INSTANCE [update]'
    exit 0
fi

XROAD_INSTANCE=${1}
LOGGER_PATH=$(/usr/local/bin/opmon-collector --xroad $XROAD_INSTANCE settings get logger.log-path)
HEARTBEAT_PATH=$(/usr/local/bin/opmon-collector --xroad $XROAD_INSTANCE settings get logger.heartbeat-path)

echo Logger path: $LOGGER_PATH

# Prepare ${LOG} and ${LOCK}
# Please note, that they depend of command ${0}
PID=$$
filename=$(basename -- "${0}")
extension="${filename##*.}"
filename="${filename%.*}"
LOG=${LOGGER_PATH}/${filename}.log
LOCK=${HEARTBEAT_PATH}/${filename}.lock

echo Logging to $LOG
echo Lockfile at $LOCK

# Begin
echo "${PID}: Start of ${0}"  2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}

# Dealing with ${LOCK}
if [ -f ${LOCK} ]; then
   echo "${PID}: Warning: Lock file ${LOCK} exists! PID = `cat ${LOCK}` -- Exiting!" 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}
   exit 1
else
   # Create it
   echo "${PID}" 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee ${LOCK}
fi

#
# Actual stuff
#
# Check if server list update is necessary
cd ${APPDIR}/${INSTANCE}

if [[ $# -eq 2 ]] ; then
    /usr/local/bin/opmon-collector --xroad $XROAD_INSTANCE update 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}
fi

# Run collector
/usr/local/bin/opmon-collector --xroad $XROAD_INSTANCE collect 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}

# Remove ${LOCK}
/bin/rm ${LOCK} 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}

# The End
echo "${PID}: End of ${0}"  2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}
cd ${CWD}
