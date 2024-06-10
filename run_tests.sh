#!/bin/bash

# sudo python3 -m pip install pytest
# pip install pytest-pep8

## Run Tests
echo "Run tests"
#pytest --cache-clear analysis_module --html=analysis_module/test_results.html --self-contained-html
#pytest --cache-clear analysis_ui_module --html=analysis_ui_module/test_results.html --self-contained-html
pytest --cache-clear anonymizer_module --html=anonymizer_module/test_results.html --self-contained-html
pytest --cache-clear collector_module --html=collector_module/test_results.html --self-contained-html
pytest --cache-clear corrector_module --html=corrector_module/test_results.html --self-contained-html
#pytest --cache-clear opendata_collector_module --html=opendata_collector_module/test_results.html --self-contained-html
pytest --cache-clear opendata_module --html=opendata_module/test_results.html --self-contained-html
pytest --cache-clear reports_module --html=reports_module/test_results.html --self-contained-html

# Run CI Tests
if [[ $1 == 'CI' ]] ; then
    echo "Test integration"
    python3 -m pytest integration_tests
fi
