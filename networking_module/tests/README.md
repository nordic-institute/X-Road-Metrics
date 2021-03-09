# Opmon Networking Module Unit Tests
## Dependencies
You need the following R libraries to run the tests:
```
R -e "install.packages('xml2', repos='https://cran.rstudio.com/')"
R -e "install.packages('testthat', repos='https://cran.rstudio.com/')"
```

## Running
```
R -e "options(testthat.output_file='test_results.xml'); testthat::test_dir('tests',reporter='junit');"
```
Results will be in JUnit format in _tests/test_results.xml_
