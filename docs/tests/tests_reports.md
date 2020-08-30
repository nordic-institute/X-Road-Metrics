
| [![Republic of Estonia Information System Authority](../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Reports Module Tests

### Test case 1: Matching documents
Description: The purpose of this test is to get all the relevant documents for the specific report.

Integration tests:

* /integration_tests/ci_reports/test_report_worker_CI.py::TestReportWorkerCI::test_get_matching_documents

Unit tests:

* Not applicable

Variations/notes:

* Documents that are not within the time frame are not queried and not returned.
* If no documents found in the time frame, no queries must be returned.
* It must be possible to use either side of the pair (client/producer) for querying.

### Test case 2: Matching documents (different cases)
Description: The purpose of this test is to test if the right documents are returned for different cases: Producer, Producer (from Client side), Client, Client (from Producer side).

Integration tests:

* /integration_tests/ci_reports/test_report_worker_CI.py::TestReportWorkerCI::test_get_matching_documents_different_cases

Unit tests:

* Not applicable

Variations/notes:

* Documents that are not within the time frame are not queried and not returned.
* If no documents found in the time frame, no queries must be returned.
* It must be possible to use either side of the pair (client/producer) for querying.

### Test case 3: Matching documents (different timestamps)
Description: The purpose of this test is to test if the right documents are returned for different time frames.

Integration tests:

* /integration_tests/ci_reports/test_report_worker_CI.py::TestReportWorkerCI::test_get_matching_documents_within_timestamp

Unit tests:

* Not applicable

Variations/notes:

* Documents that are not within the time frame are not queried and not returned.
* If no documents found in the time frame, no queries must be returned.
* It must be possible to use either side of the pair (client/producer) for querying.

### Test case 4: Sorting documents
Description: The purpose of this test is to sort documents into 4 groups: Produced services, Produced metaservices, Consumed services, Consumed metaservices.

Integration tests:

* Not applicable

Unit tests:

* /reports_module/tests/test_report_worker.py::TestReportWorker::test_sort_services

### Test case 5: Merging document fields
Description: The purpose of this test is to merge documents fields into 3 new fields: service, client, producer

Integration tests:

* Not applicable

Unit tests:

* /reports_module/tests/test_report_worker.py::TestReportWorker::test_merge_fields

Variations/notes:

* service = serviceCode.serviceVersion
* client = clientXRoadInstance/clientMemberClass/clientMemberCode/clientSubsystemCode
* producer = serviceXRoadInstance/serviceMemberClass/serviceMemberCode/serviceSubsystemCode

### Test case 6: Group by multiple keys
Description: The purpose of this test is to group the documents by multiple keys.

Integration tests:

* Not applicable
Unit tests:

* /reports_module/tests/test_report_worker.py::TestReportWorker::test_group_by_keys

### Test case 7: Calcualte averages for documents
Description: The purpose of this test is to calculate the min/avg/max values for the requestSize, responseSize & the duration.

Integration tests:

* Not applicable
Unit tests:

* /reports_module/tests/test_report_worker.py::TestReportWorker::test_group_and_merge_produced_services

### Test case 8: Test report generation
Description: The purpose of this test is to generate a report and make sure it is OK.

Integration tests:

* /integration_tests/ci_reports/test_report_worker_CI.py::TestReportWorkerCI::test_generate_report
Unit tests:

* Not applicable

Variations/notes:

* The riha.json file that the test uses is located in the /integration_tests/helpers/riha.json
* The report will be saved in the /integration_tests/ci_reports/
* The report must be identical (besides creation date & time) with the following file: /integration_tests/ci_reports/SubsystemCodeA_1970-1-1_1980-1-1_2017-10-23_17-58-13-4049.pdf
