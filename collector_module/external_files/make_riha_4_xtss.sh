#!/bin/bash
#
# Usage: make_riha_4_xtss.sh
#

SCRIPT=${0}

# We do calculate duration elapsed by script and include it as text 'Total time: HH:MM:SS' into log and heartbeat
# to do the application monitoring and find out cases when it exceeds 1h
# (/bin/cat $HEARTBEAT_FILE | grep -v 'Total time: 00:'| wc -l)
SECONDS=0

# Error handler function
error_handler(){
        ERROR_MSG=${1}
        echo ${ERROR_MSG}
        # python3 ../error_handler.py ${ERROR_MSG}
        return 1;
}

# OK handler function
ok_handler(){
        OK_MSG=${1}
        echo ${OK_MSG}
        python3 ../ok_handler.py ${OK_MSG}
        return 0;
}

if [ "${1}" == "-h" ] || [ "${1}" == "--help" ]; then
    echo -e "Usage: ${SCRIPT}
        # The IP/Name of Central Server can be found in configuration anchor http://x-road.eu/packages/
        # CENTRAL_SERVER (option -c) or SECURITY_SERVER_URL (option -s) MUST be available in ../settings.py
"
        #
        # XTEE-CI-XM
        # CENTRAL_SERVER = \"#NA\"
        # SECURITY_SERVER_URL = \"http://#NA\"
        #
        # ee-dev http://x-road.eu/packages/ee-dev_public_anchor.xml
        # CENTRAL_SERVER = \"195.80.109.140\"
        # SECURITY_SERVER_URL = \"http://#NA\"
        #
        # ee-test http://x-road.eu/packages/ee-test_public_anchor.xml
        # CENTRAL_SERVER = \"195.80.127.40\"
        # SECURITY_SERVER_URL = \"http://#NA\"
        #
        # EE http://x-road.eu/packages/EE_public-anchor.xml
        # CENTRAL_SERVER = \"213.184.41.178\"
        # SECURITY_SERVER_URL = \"http://#NA\"
# "
    exit 1;
fi

# CENTRAL_SERVER=${1}
# CENTRAL_SERVER=$(python3 ../get_settings.py CENTRAL_SERVER)
# SECURITY_SERVER_URL=${1}
SECURITY_SERVER_URL=$(python3 ../get_settings.py SECURITY_SERVER_URL)

#
# Input file: riha_systems.json, configurable as parameter --riha <filename>
# Output file: riha_4_xtss.json, hardcoded into ./subsystems_json_riha_4_xtss.py
#
INPUT_RIHA="./riha_systems.json"
OUTPUT_RIHA="./riha_4_xtss.json"

# Check existence of ${INPUT_RIHA}
if [ ! -f "${INPUT_RIHA}" ]; then
    echo "`date "+[%F %T]"` ERROR: File ${INPUT_RIHA} does not exist! Exiting ..."
	exit 1
fi

# Make a backup of result file ${OUTPUT_RIHA}
if [[ $(find ${OUTPUT_RIHA} -type f -size +100c 2>/dev/null) ]]; then
    /bin/cp --preserve ${OUTPUT_RIHA} ${OUTPUT_RIHA}.bak
else
    echo "`date "+[%F %T]"` Warning: Size of ${OUTPUT_RIHA} was less than 100 bytes. Do not make backup"
fi

# Do the job
python3 ./subsystems_json_riha_4_xtss.py -s ${SECURITY_SERVER_URL} --riha ${INPUT_RIHA} # && \
# python3 ./subsystems_json_riha_4_xtss.py -c ${CENTRAL_SERVER} --riha ${INPUT_RIHA} # && \
#     ok_handler "INFO: ${SCRIPT} while make ${OUTPUT_RIHA}" || \
#     error_handler "ERROR: ${SCRIPT} while make ${OUTPUT_RIHA}"

RESULT_CODE=$?
# duration=${SECONDS}; TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "${duration}"`;
TOTAL_TIME=`TZ=UTC0 printf 'Total time: %(%H:%M:%S)T\n' "${SECONDS}"`;
if [ ${RESULT_CODE} -eq 0 ]
then
    # Specific for RIA
    # TMP="/tmp/$$"
    # cat ${OUTPUT_RIHA} | sed -e "s/\"email\": \[\]/\"email\": \[ \{\"name\": \"RIA kasutajatugi\", \"email\": \"help@ria.ee\"\}, \{\"name\": \"opmon-xtss\", \"email\": \"toomas.molder@ria.ee\"\} \]/" > ${TMP} && mv ${TMP} ${OUTPUT_RIHA}

    # Check, printout
    # echo "`date "+[%F %T]"` Info: Number of subsystems: `cat ${OUTPUT_RIHA} | egrep "subsystem_code" | wc -l`"
    # echo "`date "+[%F %T]"` Info: Number of subsystems without contact: `cat ${OUTPUT_RIHA} | egrep "\"email\": \[ {\"name\": \"RIA kasutajatugi\", \"email\": \"help@ria.ee\"} \]" | wc -l`"
    # echo "`date "+[%F %T]"` Info: Number of subsystems without contact: `cat ${OUTPUT_RIHA} | egrep "RIA kasutajatugi" | wc -l`"
    ok_handler "INFO: ${SCRIPT} while make ${OUTPUT_RIHA}, ${TOTAL_TIME}"
else
    # Check the result file ${OUTPUT_RIHA}, restore from backup if needed
    if [[ $(find ${OUTPUT_RIHA} -type f -size -100c 2>/dev/null) ]]; then
       /bin/cp --preserve ${OUTPUT_RIHA}.bak ${OUTPUT_RIHA}
       echo "`date "+[%F %T]"` Warning: Size of ${OUTPUT_RIHA} was less than 100 bytes. Restore from backup"
    fi
    error_handler "ERROR: ${SCRIPT} while make ${OUTPUT_RIHA}, ${TOTAL_TIME}"
fi
