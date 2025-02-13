license:
	@echo "Checking if licenseheaders library is installed..."
	@if pip show licenseheaders > /dev/null 2>&1; then \
		echo "licenseheaders is installed."; \
	else \
		echo "licenseheaders is not installed. Installing it..."; \
		pip install licenseheaders --no-input; \
	fi
	@echo "Adding license to integration_tests..."
	@licenseheaders -t ../LICENSE.MD -E py
	@echo "License added."
