
| [![Republic of Estonia Information System Authority](../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Corrector Tests

### Test case 1: Client calculations
Description: The purpose of this test is to ensure that all the client side calculations are correct.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_client_calculations

Variations/notes:

* The calculation results are stored in values that need to be added to the document.

### Test case 2: Producer calculations
Description: The purpose of this test is to ensure that all the producer side calculations are correct.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_producer_calculations

Variations/notes:

* The calculation results are stored in values that need to be added to the document.

### Test case 3: Pair calculations
Description: The purpose of this test is to ensure that all the calculations that are connected with client and producer are correct.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_pair_calculations

Variations/notes:

* The calculation results are stored in values that need to be added to the document.

### Test case 4: All the calculations together
Description: The purpose of this test is to ensure that all the calculations are correct.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_apply_calculations

Variations/notes:

* The calculation results are stored in values that need to be added to the document.

### Test case 5: Match documents
Description: The purpose of this test is to test all the possible matching conditions.

Integration tests:

* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_simple_pair_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_pair_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_batch_pair_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_simple_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_batch_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_simple_all_producer_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_all_producer_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_simple_orphan_pair_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_orphan_pair_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_many_matchingType_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_producer_matching_with_orphan_client
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_client_matching_with_orphan_producer
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_producer_orphan_matching_with_orphan_client
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_client_orphan_matching_with_orphan_producer
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_pair_match_with_duplicate_messageId

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_match_documents

Variations/notes:

* Both the regular and orphan matching is covered within this test.

### Test case 6: Hash calculation
Description: The purpose of this test is to test the hash calculations.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_calculate_hash
* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_calculate_hash_variation
Variations/notes:

* The uniqueness is combined of the hash + the "monitoringDataTs" parameter.

### Test case 7: Match documents
Description: The purpose of this test is to test all the possible matching conditions.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_find_match

Variations/notes:

* Both the regular and orphan matching is covered within this test.

### Test case 8: Document creation
Description: The purpose of this test is to test the creation of a document with correct fields.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_create_json

Variations/notes:

* The fields are the following: "client", "producer", "clientHash", "producerHash" and "messageId".

### Test case 9: Document structure
Description: The purpose of this test is to ensure that the structure of all the documents would be the same.

Integration tests:

* Not applicable.

Unit tests:

* /corrector_module/tests/test_document_manager.py::TestDocumentManager::test_correct_structure

Variations/notes:

* The documents without "securityServerType" are considered as "Client".

### Test case 10: Find duplicates
Description: The purpose of this test is to find all the duplicates.

Integration tests:


* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_simple_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_batch_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_simple_all_producer_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_multiple_all_producer_duplicates_match
* /integration_tests/ci_corrector/test_corrector.py::TestCorrectorCI::test_pair_match_with_duplicate_messageId

Unit tests:

* Not applicable.

Variations/notes:

