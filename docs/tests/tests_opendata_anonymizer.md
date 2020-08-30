
| [![Republic of Estonia Information System Authority](../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Open Data Anonymizer Tests

### Test case 1: Parsing configuration
Description: The purpose of this test is to verify that parameters from configuration files are read and parsed correctly.

Integration tests:

* Not applicable

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_allowed_fields_parsing
* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_hiding_rules_parsing
* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_hiding_rules_parsing
* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_substitution_rules_parsing
* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_transformers_parsing
* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_field_translation_parsing
* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_field_value_mask_parsing


### Test case 2: Storing and accessing the last Anonymizer run's timestamp
Description: The purpose of this test is to verify that Anonymizer stores its timestamp successfully and that it is retrievable later on.

Integration tests:

* Not applicable

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymizer.py::TestAnonymizer::test_last_anonymization_timestamp_storing

Variations/notes:

* Last timestamp is stored in a SQLite database file to prevent accidental corruption.
* Storing and accessing the correct timestamp is crucial for scheduled anonymization jobs, as it determines, which raw logs must be fetched from MongoDB.
* The timestamp value is defined at the beginning of the anonymization session and is used as a maximum timestamp when fetching raw logs. This prevents eternal sessions, should the data arrive to MongoDB at least at the same speed as Anonymizer processses.


### Test case 3: Hiding logs based on regular expressions
Description: The purpose of this test is to verify that the function detecting logs, which should be hidden (not available for public use) given the hiding rules, works as expected.

Integration tests:

* Not applicable

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymization_job.py::TestAnonymizationJob::test_record_hiding_with_rules
* /opendata_module/anonymizer/tests/test_anonymization_process.py::TestAnonymizationProcess::test_anonymizing_with_hiding_rules

Variations/notes:

* Tested on a fabricated use case, which will detect, if the function works as expected.
* Tested on a small subset of development data.


### Test case 4: Substituting log's values
Description: The purpose of this test is to verify that the function substituting specific feature values with static ones works as expected.

Integration tests:

* Not applicable

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymization_job.py::TestAnonymizationJob::test_record_substitution
* /opendata_module/anonymizer/tests/test_anonymization_process.py::TestAnonymizationProcess::test_anonymizing_with_substitution_rules

Variations/notes:

* Tested on a fabricated use case, which will detect, if the function works as expected.
* Tested on a small subset of development data.


### Test case 5: Separating client and producer logs from raw dual log
Description: Clean data collection in MongoDB stores client-producer pairs as a single document. In Open Data Module, client and producer logs are kept separately. This test verifies that common and distinct features end up in the correct agent's log record.

Integration tests:

* Not applicable

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymization_job.py::TestAnonymizationJob::test_dual_record_splitting

Variations/notes:

* Tested on a representative subset of the real features.


### Test case 6: Anonymizing without new raw logs
Description: The purpose of this test is to verify that nothing breaks and no logs leak, when no new logs are available in MongoDB.

Integration tests:

* /integration_tests/ci_anonymizer/test_anonymizer.py::TestAnonymizationCI::test_anonymizing_no_documents

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymization_process.py::TestAnonymizationProcess::test_anonymizing_without_documents


### Test case 7: Anonymizing without constraints
Description: The purpose of this test is to check that the base processing pipeline is working - the documents that go in, come out with just the client and producer data separated.

Integration tests:

* Not applicable

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymization_process.py::TestAnonymizationProcess::test_anonymizing_without_constraints

Variations/notes:

* Tested on a small subset of development data.


### Test case 8: Anonymizing with requestInTs precision reduction
Description: The purpose of this test is to check that loading custom transformers, and the one reducing requestInTs precision more specifically, works.

Integration tests:

* Not applicable

Unit tests:

* /opendata_module/anonymizer/tests/test_anonymization_process.py::TestAnonymizationProcess::test_anonymizing_with_time_precision_reduction

Variations/notes:

* Tested on a small subset of development data.


### Test case 9: Ignoring irrelevant logs during anonymization
Description: In order to avoid duplicates in the Open Data PostgreSQL database, still changing or already processed raw logs must be ignored. This test verifies that only relevant logs are fetched.

Integration tests:

* /integration_tests/ci_anonymizer/test_anonymizer.py::TestAnonymizationCI::test_ignoring_processing_documents
* /integration_tests/ci_anonymizer/test_anonymizer.py::TestAnonymizationCI::test_done_and_processing_documents
* /integration_tests/ci_anonymizer/test_anonymizer.py::TestAnonymizationCI::test_anonymizing_outdated_documents

Unit tests:

* Not applicable

Variations/notes:

* Tested on a small subset of development data.


### Test case 10: Single anonymization session
Description: The purpose of this test is to verify that the full pipeline - data from MongoDB moves through Anonymizer to PostgreSQL Open Data database - works as expected. This involves applying aforetested anonymization procedures to relevant and irrelevant logs.

Integration tests:

* /integration_tests/ci_anonymizer/test_anonymizer.py::TestAnonymizationCI::test_anonymizing_documents

Unit tests:

* Not applicable

Variations/notes:

* Tested on a small subset of development data.

### Test case 11: Simulate a scheduled anonymization job
Description: The purpose of this test is to simulate a scheduled anonymization job and verify that consecutive anonymization sessions with new data process the correct data subset.

Integration tests:

* /integration_tests/ci_anonymizer/test_anonymizer.py::TestAnonymizationCI::test_scheduled_anonymization

Unit tests:

* Not applicable

Variations/notes:

* Tested on a small subset of development data.