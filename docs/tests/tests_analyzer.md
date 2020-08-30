
| [![Republic of Estonia Information System Authority](../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Analyzer Tests

### Test case 1: Finding anomalies from aggregated data
Description: The purpose of this test is to check if the number of found anomalies is correct, given data that is already aggregated by time periods.

Integration tests:

* Not applicable

Unit tests:

* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_failed_request_ratio_model_empty_dataframe
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_duplicate_message_id_model_empty_dataframe
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_time_sync_model_empty_dataframe
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_transform_empty_dataframe
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_failed_request_ratio_model_anomaly_not_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_duplicate_message_id_model_anomaly_not_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_time_sync_model_anomaly_not_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_transform_anomaly_not_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_failed_request_ratio_model_anomaly_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_duplicate_message_id_model_anomaly_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_time_sync_model_anomaly_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_transform_anomaly_found
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_transform_period_not_in_model


Variations/notes:

* If the aggregated data do not contain any entries, the number of returned anomalies must be 0.
* If there are entries in the aggregated data, but no anomalies exist among them, the number of returned anomalies must be 0.
* If there are entries in the aggregated data and an anomaly exists, the number of returned anomalies must be 1.
* For the historic averages model, if the respective "similar" time period for the given service call does not exist in the model, the number of returned anomalies must be 1.


### Test case 2: Training the historic averages model based on aggregated data
Description: The purpose of this test is to check if the historic averages are calculated correctly, given data that is already aggregated by time periods.

Integration tests:

* Not applicable

Unit tests:

* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_fit_empty_dataframe
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_fit_single_query
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_fit_two_queries


Variations/notes:

* If the aggregated data do not contain any entries, the model must contain 0 rows.
* If a single entry exists in the aggregated data, the historic average must be set as this value and the std must be set to 0.
* If several entries exist in the aggregated data about the same service call and "similar" time period, the historic average (std) must be set as the average (std) of these entries.


### Test case 3: Updating the historic averages model based on aggregated data
Description: The purpose of this test is to check if the historic averages are updated correctly, given data that is already aggregated by time periods.

Integration tests:

* Not applicable

Unit tests:

* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_update_empty_dataframe
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_update_existing_period
* /analysis_module/analyzer/tests/test_analyzer_models.py::TestAnalyzerModels::test_averages_by_timeperiod_model_add_new_period


Variations/notes:

* If the aggregated data do not contain any entries, the model must remain unchanged.
* If the model already contains an entry for the "similar" time period for the given service call to be updated, no rows should be added to the model, but the values in the relevant row must be updated.
* If the model does not contain an entry for the "similar" time period for the given service call to be updated, a new row must be added to the model.


### Test case 4: Aggregating data by time periods
Description: The purpose of this test is to check if the documents in the clean_data collection are aggregated correctly for the models.

Integration tests:

* all tests in the TestCase /integration_tests/ci_analyzer/test_analyzer_aggregation_queries.py::TestAnalyzerAggregationQueriesCI

Unit tests:

* Not applicable

Variations/notes:

* If there are no documents in the database, the aggregated data should contain 0 rows.
* It must be possible to use either side of the pair (client/producer) for querying.
* If ``start_time`` is specified, only documents with ``requestInTs`` >= ``start_time`` must be considered.
* If ``end_time`` is specified, only documents with ``requestInTs`` < ``end_time`` must be considered.
* If ``ids_to_exclude`` is specified, documents with the respective ids should be excluded. 
* For failed_request_ratio model:
	* If there exists a single document for a given time period and service call, the aggregated data should contain 1 row.
	* If there exist several documents for the same time period and service call but all are of the same type (all are succeeded or all are not succeeded), the aggregated data should contain 1 row.
	* if there exist several documents for the same time period and service call, but some of them are succeeded and others are not, the aggregated data should contain 2 rows.
* For duplicated_message_id model:
	* If one or several documents exist in the time period, but all message ids are different, the aggregated data should contain 0 rows.
	* If two queries in the same time period and same service call have the same message id, the aggregated data should contain 1 row.
	* If two queries have the same service call and same message id, but are from different time periods, the aggregated data should contain 0 rows.
* For time_sync_model model:
	* If one or several documents exist in the time period, but none of them violate the time sync constraint, the aggregated data should contain 0 rows.
	* If two queries in the same time period and same service call have the same message id, and at least one of them violates the time sync constraint, the aggregated data should contain 1 row.
* For historic_averages_model model:
	* If one or several documents exist in the time period for the same service call, the aggregated data should contain 1 row (even if no anomalies exist).
	* Documents where ``succeeded=False`` should be excluded.
	* If two documents with the same service call fall into different time periods, the aggregated data should contain 2 rows.
	* If two documents in the same time period have different service calls, the aggregated data should contain 2 rows.

	
### Test case 5: Determining service call stages for training
Description: The purpose of this test is to check if the correct stage is detected for each service call for training/updating of historic averages models.

Integration tests:

* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_train_stages_empty_clean_data
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_train_stages_regular
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_train_stages_retrain
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_train_stages_first_train
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_train_stages_none


Unit tests:

* Not applicable

Variations/notes:

* If the service call is not present in the service_call_first_timestamps collection, the service call is not qualified for model training.
* If ``first_request_timestamp`` is present, ``first_model_train_timestamp`` is missing, and less than 3 months have passed since the first_request_timestamp, the service call is not qualified for model training.
* If ``first_request_timestamp`` is present, ``first_model_train_timestamp`` is missing, and at least 3 months have passed since the first_request_timestamp, the service call is in stage "first model training".
* If ``first_model_train_timestamp`` is present, ``first_model_retrain_timestamp`` is missing, and at least 10 days have passed since ``first_incident_timestamp``, the service call is in stage "model retraining".
* If ``first_model_retrain_timestamp`` is present, the service call is in "regular" phase.


### Test case 6: Retrieving training data according to service call stages
Description: The purpose of this test is to check if the correct training data is retrieved for each service call according to its stage.

Integration tests:

* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_data_for_train_stages_empty_data
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_data_for_train_stages_regular
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_data_for_train_stages_regular_incident

Unit tests:

* Not applicable

Variations/notes:

* If there are no service calls in any of the relevant stages, the number of rows in the retrieved data should be 0.
* If a service call is in "regular" stage and a relevant document exists in a time period between the last model update timestamp and the current timestamp (considering corrector buffer time), 1 row should be returned.
* If same as previous, but the document is part of an anomaly that was marked as "incident", 0 rows should be returned.

### Test case 7: Determining service call stages for anomaly finding
Description: The purpose of this test is to check if the correct stage is detected for each service call for finding anomalies using historic averages models.

Integration tests:

* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_transform_stages_none
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_transform_stages_first_incident
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_service_calls_for_transform_stages_regular

Unit tests:

* Not applicable

Variations/notes:

* If ``first_model_train_timestamp`` is missing, the service call is not qualified for anomaly finding (number of returned rows is 0).
* If ``first_model_train_timestamp`` is present, but ``first_incident_timestamp`` is missing, the service call is in "first incident" stage.
* If ``first_model_retrain_timestamp`` is present, the service call is in "regular" stage. 


### Test case 8: Retrieving data for finding anomalies according to service call stages
Description: The purpose of this test is to check if the correct data is retrieved for each service call according to its stage for finding anomalies.

Integration tests:

* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_data_for_transform_stages_empty_data
* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_get_data_for_transform_stages_regular

Unit tests:

* Not applicable

Variations/notes:

* If there are no service calls in any of the relevant stages, the number of rows in the retrieved data should be 0.
* If a service call is in "regular" stage and a relevant document exists in a time period between the last anomaly finding timestamp and the current timestamp (considering corrector buffer time), 1 row should be returned.


### Test case 9: Adding first request timestamps from clean data
Description: The purpose of this test is to check if the first request timestamps are retrieved correctly from the clean data.

Integration tests:

* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_add_first_request_timestamps_from_clean_data

Unit tests:

* Not applicable

Variations/notes:

* If 3 months have passed since the first timestamp that has just been added, the service call should enter the "first model" stage.


### Test case 10: Updating first training and retraining timestamps
Description: The purpose of this test is to check if the timestamps are updated correctly after training the first or second model for a service call.

Integration tests:

* /integration_tests/ci_analyzer/test_analyzer_timeperiods.py::TestAnalyzerTimeperiodsCI::test_update_first_train_retrain_timestamps

Unit tests:

* Not applicable

Variations/notes:

* The updated timestamp for first model training should correspond to the value that was just used for updating.