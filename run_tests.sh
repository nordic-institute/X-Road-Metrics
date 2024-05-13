#!/bin/bash

# sudo python3 -m pip install pytest
# pip install flake8

export REPORTS_RUN_ENV="REPORTS_TEST"

#set -e

# Run Pep8 Tests
ruff check collector_module
ruff check corrector_module
ruff check reports_module/opmon_reports/report_manager.py
#ruff check analysis_ui_module
#ruff check analysis_module
ruff check anonymizer_module

## Run Tests
pytest --cache-clear collector_module --html=collector_module/test_results.html --self-contained-html
pytest --cache-clear corrector_module --html=corrector_module/test_results.html --self-contained-html
pytest --cache-clear reports_module --html=reports_module/test_results.html --self-contained-html
#pytest --cache-clear analysis_ui_module --html=analysis_ui_module/test_results.html --self-contained-html
#pytest --cache-clear analysis_module --html=analysis_module/test_results.html --self-contained-html
pytest --cache-clear opendata_module/anonymizer --html=opendata_module/anonymizer/test_results.html --self-contained-html

# Run CI Tests
if [[ $1 == 'CI' ]] ; then
    echo "Test integration"
    python3 -m pytest integration_tests
fi
