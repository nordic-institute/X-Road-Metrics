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

# APPDIR="/srv/app"
APPDIR=$(python3 get_settings.py APPDIR)
# Change INSTANCE if needed!
INSTANCE=$(python3 get_settings.py INSTANCE)

# Prepare ${LOG} and ${LOCK}
# Please note, that they depend of command ${0}
PID=$$
filename=$(basename -- "${0}")
extension="${filename##*.}"
filename="${filename%.*}"
LOG=${APPDIR}/${INSTANCE}/logs/${filename}.log
LOCK=${APPDIR}/${INSTANCE}/heartbeat/${filename}.lock

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

if [[ $# -eq 1 ]] ; then
    python3 -m collector_module.update_servers 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}
fi

# Run collector
python3 -m collector_module.collector 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}

# Remove ${LOCK}
/bin/rm ${LOCK} 2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}

# The End
echo "${PID}: End of ${0}"  2>&1 | awk '{ print strftime("%Y-%m-%dT%H:%M:%S\t"), $0; fflush(); }' | tee -a ${LOG}
cd ${CWD}
