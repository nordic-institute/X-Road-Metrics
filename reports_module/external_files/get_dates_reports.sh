#!/bin/bash
TODAY=$(date '+%F') # or whatever YYYY-MM-DD you need
THIS_MONTH_START=$(date -d "$TODAY" '+%Y-%m-01')
LAST_MONTH_START=$(date -d "$THIS_MONTH_START -1 month" '+%F')
LAST_MONTH_END=$(date -d "$LAST_MONTH_START +1 month -1 day" '+%F')
echo $LAST_MONTH_START $LAST_MONTH_END
