clean:
	@echo "Cleaning project..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f ./test_results.xml
	@rm -rf .coverage
	@rm -rf .tox/
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf opmon_collector/tests/responses/Test/
	@rm -rf ../htmlcov/collector_module/
	@echo "Project cleaned."

license:
	@echo "Checking if licenseheaders library is installed..."
	@if pip show licenseheaders > /dev/null 2>&1; then \
		echo "licenseheaders is installed."; \
	else \
		echo "licenseheaders is not installed. Installing it..."; \
		pip install licenseheaders --no-input; \
	fi
	@echo "Adding license to opmon_collector module..."
	@licenseheaders -t ../LICENSE.MD -E py -d ./opmon_collector
	@echo "Adding license to opmon_mongodb_maintenance module..."
	@licenseheaders -t ../LICENSE.MD -E py -d ./opmon_mongodb_maintenance
	@echo "Note: bin directory is not updated by the tool. Make sure to update it manually."
	@echo "License added."
