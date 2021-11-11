#!/bin/bash 
#
# X-Road Metrics Networking script to update data periodically using cron
#
# Maintained by NIIS (info@niis.org)

PROFILE=${1:-""}

PROFILE_FLAG=""
if [[ -n "$PROFILE" ]]; then PROFILE_FLAG="--profile $PROFILE"; fi;

PROFILE_SUFFIX=""
if [[ -n "$PROFILE" ]]; then PROFILE_SUFFIX="_$PROFILE"; fi;

# Prepare ${LOG} and ${LOCK}
# Please note, that they depend of command ${0}
PID=$$
filename=$(basename -- "${0}")
filename="${filename%.*}${PROFILE_SUFFIX}"
LOG=/var/log/xroad-metrics/networking/logs/${filename}.log
LOCK=/var/log/xroad-metrics/networking/heartbeat/${filename}.lock

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
Rscript /usr/bin/xroad-metrics-networking $PROFILE_FLAG 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}

# Remove ${LOCK}
/bin/rm ${LOCK} 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}

# The End
echo "${PID}: End of ${0}"  2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}
