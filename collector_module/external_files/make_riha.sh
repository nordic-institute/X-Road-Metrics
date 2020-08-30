#!/bin/bash
#
# Usage: make_riha.sh
#

SCRIPT=${0}
TOTAL_DURATION=0

# Error handler function
error_handler(){
        ERROR_MSG=${1}
        echo ${ERROR_MSG}
        python3 ../error_handler.py ${ERROR_MSG}
        return 1;
}

# OK handler function
ok_handler(){
        OK_MSG=${1}
        echo ${OK_MSG}
        python3 ../ok_handler.py ${OK_MSG}
        return 0;
}

APPDIR=$(python3 ../get_settings.py APPDIR)
INSTANCE=$(python3 ../get_settings.py INSTANCE)

reports_user="reports"
reports_server="#NA"
reports_target_dir="${APPDIR}/${INSTANCE}/reports_module/external_files"
reports_target_file="riha.json"

networking_user="networking"
networking_server="#NA"
networking_target_dir="${APPDIR}/${INSTANCE}/networking_module"
networking_target_file="riha_${INSTANCE}.json"

networking_www_user=${networking_user}
networking_www_server=${networking_server}
networking_www_target_dir="/srv/shiny-server/${INSTANCE}/www"
networking_www_target_file="riha.json"

# Actual stuff
# We do calculate duration elapsed by script and include it as text 'Total time: HH:MM:SS' into log and heartbeat
# to do the application monitoring and find out cases when it exceeds 1h
# (/bin/cat $HEARTBEAT_FILE | grep -v 'Total time: 00:'| wc -l)
SECONDS=0

# Into reports module ..., name as riha.json
cd ${APPDIR}/${INSTANCE}/collector_module/external_files
./make_riha_4_reports.sh
scp -p riha_4_reports.json  ${reports_user}@${reports_server}:${reports_target_dir}/${reports_target_file} # && \
#     { duration=$SECONDS; TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "$duration"`; \
#         ok_handler "INFO: ${SCRIPT} while scp ${reports_user}@${reports_server}, ${TOTAL_TIME}" ; } || \
#     { duration=$SECONDS; TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "$duration"`; \
#         error_handler "ERROR: ${SCRIPT} while scp ${reports_user}@${reports_server}, ${TOTAL_TIME}" ; }

SCP_REPORTS_RESULT_CODE=$?
duration=${SECONDS}; TOTAL_DURATION=$((${TOTAL_DURATION} + ${duration}))
REPORTS_TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "${duration}"`;
if [ ${SCP_REPORTS_RESULT_CODE} -eq 0 ]
then
    ok_handler "INFO: ${SCRIPT} while scp ${reports_user}@${reports_server}, ${REPORTS_TOTAL_TIME}"
else
    error_handler "ERROR: ${SCRIPT} while scp ${reports_user}@${reports_server}, ${REPORTS_TOTAL_TIME}"
fi

# Into networking module ..., name as riha_$instance.json
SECONDS=0
cd ${APPDIR}/${INSTANCE}/collector_module/external_files
./make_riha_4_networking.sh
scp -p riha_4_networking.json ${networking_user}@${networking_server}:${networking_target_dir}/${networking_target_file} # && \
#     { duration=$SECONDS; TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "$duration"`; \
#         ok_handler "INFO: ${SCRIPT} while scp ${networking_user}@${networking_server}, ${TOTAL_TIME}" ; } || \
#     { duration=$SECONDS; TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "$duration"`; \
#         error_handler "ERROR: ${SCRIPT} while scp ${networking_user}@${networking_server}, ${TOTAL_TIME}" ; }

SCP_NETWORKING_RESULT_CODE=$?
duration=${SECONDS}; TOTAL_DURATION=$((${TOTAL_DURATION} + ${duration}))
NETWORKING_TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "${duration}"`;
if [ ${SCP_NETWORKING_RESULT_CODE} -eq 0 ]
then
    ok_handler "INFO: ${SCRIPT} while scp ${networking_user}@${networking_server}, ${NETWORKING_TOTAL_TIME}"
else
    error_handler "ERROR: ${SCRIPT} while scp ${networking_user}@${networking_server}, ${NETWORKING_TOTAL_TIME}"
fi

# Into networking_www module ..., name same as riha.json
SECONDS=0
cd ${APPDIR}/${INSTANCE}/collector_module/external_files
./make_riha_4_networking_www.sh
scp -p riha_4_networking_www.json ${networking_www_user}@${networking_www_server}:${networking_www_target_dir}/${networking_www_target_file} # && \
#     { duration=$SECONDS; TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "$duration"`; \
#         ok_handler "INFO: ${SCRIPT} while scp ${networking_www_user}@${networking_www_server}, ${TOTAL_TIME}" ; } || \
#     { duration=$SECONDS; TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "$duration"`; \
#         error_handler "ERROR: ${SCRIPT} while scp ${networking_www_user}@${networking_www_server}, ${TOTAL_TIME}" ; }

SCP_NETWORKING_WWW_RESULT_CODE=$?
duration=${SECONDS}; TOTAL_DURATION=$((${TOTAL_DURATION} + ${duration}))
NETWORKING_WWW_TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "${duration}"`;
if [ ${SCP_NETWORKING_WWW_RESULT_CODE} -eq 0 ]
then
    ok_handler "INFO: ${SCRIPT} while scp ${networking_www_user}@${networking_www_server}, ${NETWORKING_WWW_TOTAL_TIME}"
else
    error_handler "ERROR: ${SCRIPT} while scp ${networking_www_user}@${networking_www_server}, ${NETWORKING_WWW_TOTAL_TIME}"
fi

TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "${TOTAL_DURATION}"`;
RESULT_CODE=$((${SCP_REPORTS_RESULT_CODE} + ${SCP_NETWORKING_RESULT_CODE} + ${SCP_NETWORKING_WWW_RESULT_CODE}))
if [ ${RESULT_CODE} -eq 0 ]
then
    ok_handler "INFO: ${SCRIPT} scp, ${TOTAL_TIME}"
else
    error_handler "ERROR: ${SCRIPT} scp, ${TOTAL_TIME}"
fi

