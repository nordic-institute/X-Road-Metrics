#!/bin/bash

# Stop script if error
# set -e 1

# Error handler function
error_handler(){
        ERROR_MSG=${1}
        echo ${ERROR_MSG}
        python3 error_handler.py ${ERROR_MSG}
        exit 1;
}

# OK handler function
ok_handler(){
        OK_MSG=${1}
        echo ${OK_MSG}
        python3 ok_handler.py ${OK_MSG}
        return 0;
}

INSTANCE=$(python3 get_settings.py INSTANCE) || error_handler "${0}: Error while getting INSTANCE"
REPORTS_PATH=$(python3 get_settings.py REPORTS_PATH) || error_handler "${0}: Error while getting REPORTS_PATH"
REPORTS_TARGET=$(python3 get_settings.py REPORTS_TARGET) || error_handler "${0}: Error while getting REPORTS_TARGET"

echo "`date "+[%F %T]"` Start ${0}"

#
# Run reports
#

echo "`date "+[%F %T]"` Run reports ..."
cd ..
python3 -m reports_module.report --language et || error_handler "${0}: Error while python3 -m reports_module.report --language et"
echo "`date "+[%F %T]"` ... Done."

#
# Publish reports
#

echo "`date "+[%F %T]"` Publish reports ..."
cd ./reports_module

# Use settings
# REPORTS_TARGET="${publishing_user}@${publishing_server}:${reports_publishing_directory}/${INSTANCE}/"
/usr/bin/rsync --quiet --times --compress --recursive --prune-empty-dirs --include='*.pdf' --include='*/' --exclude='*' ${REPORTS_PATH} ${REPORTS_TARGET} || error_handler "${0}: Error while publishing into ${REPORTS_TARGET}"

#
# Run notification manager
#
echo "`date "+[%F %T]"` Run notification manager ..."
cd ..
python3 -m reports_module.notifications || error_handler "${0}: Error while python3 -m reports_module.notifications"
echo "`date "+[%F %T]"` ... Done."

#
# The End
#
cd ./reports_module
ok_handler "`date "+[%F %T]"` End ${0}"
exit