#!/bin/bash

# pip install pytest
# pip install ruff

export REPORTS_RUN_ENV="REPORTS_TEST"

#set -e

# Run Pep8 Tests
#ruff check analysis_module
#ruff check analysis_ui_module
ruff check anonymizer_module
ruff check collector_module
ruff check corrector_module
ruff check opendata_collector_module
ruff check opendata_module
ruff check reports_module

## Run Tests
#pytest --cache-clear --ruff analysis_module --html=analysis_module/test_results.html --self-contained-html
#pytest --cache-clear --ruff analysis_ui_module --html=analysis_ui_module/test_results.html --self-contained-html
pytest --cache-clear --ruff anonymizer_module --html=anonymizer_module/test_results.html --self-contained-html
pytest --cache-clear --ruff collector_module --html=collector_module/test_results.html --self-contained-html
pytest --cache-clear --ruff corrector_module --html=corrector_module/test_results.html --self-contained-html
#pytest --cache-clear --ruff opendata_collector_module --html=opendata_collector_module/test_results.html --self-contained-html
pytest --cache-clear --ruff opendata_module --html=opendata_module/test_results.html --self-contained-html
pytest --cache-clear --ruff reports_module --html=reports_module/test_results.html --self-contained-html

# Run CI Tests
if [[ $1 == 'CI' ]] ; then
    echo "Test integration"
    python3 -m pytest integration_tests
fi
