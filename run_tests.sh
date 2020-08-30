#!/bin/bash

# sudo python3 -m pip install pytest
# pip install pytest-pep8

export REPORTS_RUN_ENV="REPORTS_TEST"

set -e

# Run Pep8 Tests
python3 -m pytest --pep8 -m pep8 collector_module --ignore=collector_module/external_files
python3 -m pytest --pep8 -m pep8 corrector_module
python3 -m pytest --pep8 -m pep8 reports_module
# python3 -m pytest --pep8 -m pep8 analysis_module/analyzer_ui
# python3 -m pytest --pep8 -m pep8 analysis_module/analyzer
python3 -m pytest --pep8 -m pep8 opendata_module/anonymizer

# echo "Test Corrector"
# python3 -m pytest corrector_module

echo "Test Reports"
python3 -m pytest reports_module
# python3 -m pytest analysis_module/analyzer_ui
# python3 -m pytest analysis_module/analyzer
python3 -m pytest opendata_module/anonymizer
# python3 -m pytest opendata_module/interface

# Run CI Tests
if [[ $1 == 'CI' ]] ; then
    echo "Test integration"
    python3 -m pytest integration_tests
fi

# Test Open Data interface's input validation
# python3 -m pytest opendata_module/interface/
