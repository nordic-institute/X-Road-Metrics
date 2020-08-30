#!/bin/bash

APPDIR="/srv/app" 
INSTANCE="sample" 

cd ${APPDIR}/${INSTANCE}/analysis_module/analyzer 

python3 train_or_update_historic_averages_models.py 2>&1 | while IFS= read -r line; do printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"; done >> ${APPDIR}/${INSTANCE}/logs/train_or_update_historic_averages_models.log ; 

python3 find_anomalies.py 2>&1 | while IFS= read -r line; do printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"; done >> ${APPDIR}/${INSTANCE}/logs/find_anomalies.log
