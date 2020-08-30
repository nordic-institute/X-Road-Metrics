# service_call_fields = ["clientMemberClass", "clientMemberCode", "clientXRoadInstance", "clientSubsystemCode", "serviceCode",
#                        "serviceVersion", "serviceMemberClass", "serviceMemberCode", "serviceXRoadInstance",
#                       "serviceSubsystemCode"]
service_call_fields = ["clientXRoadInstance", "clientMemberClass", "clientMemberCode", "clientSubsystemCode", 
                       "serviceXRoadInstance", "serviceMemberClass", "serviceMemberCode", "serviceSubsystemCode", 
                       "serviceCode", "serviceVersion"]

historic_averages_anomaly_types = ["request_count", "mean_request_size", "mean_response_size", "mean_client_duration",
                                   "mean_producer_duration"]

# NEW INCIDENTS TABLE #

new_incident_columns = [(field, field, "categorical", None, None) for field in service_call_fields]
new_incident_columns += [("anomalous metric", "anomalous_metric", "categorical", None, None),
                         ("anomaly confidence", "anomaly_confidence", "numeric", 2, None),
                         ("period start time", "period_start_time", "date", None, "%a %Y-%m-%d %H:%M"),
                         ("aggregation timeunit", "aggregation_timeunit", "categorical", None, None),
                         ("monitored metric value", "monitored_metric_value", "numeric", 2, None),
                         ("difference from normal", "difference_from_normal", "numeric", 2, None),
                         ("request count", "request_count", "numeric", 0, None),
                         ("description", "description", "text", None, None),
                         ("comments", "comments", "text", None, None)]

# new_incident_order = [["request_count", "desc"]]
new_incident_order = [["anomaly_confidence", "desc"], ["request_count", "desc"], ["period_start_time", "desc"]]

# HISTORICAL INCIDENTS TABLE #

historical_incident_columns = new_incident_columns[:-1]
historical_incident_columns += [("incident status", "incident_status", "categorical", None, None),
                                ("incident update timestamp", "incident_update_timestamp", "date", None, "%a %Y-%m-%d %H:%M")]

historical_incident_order = [["incident_update_timestamp", "desc"]]

# EXAMPLE REQUESTS TABLE #

relevant_fields_for_example_requests_general = ['totalDuration', 'producerDurationProducerView']
relevant_fields_for_example_requests_nested = ['messageId', 'requestInTs', 'succeeded']
relevant_fields_for_example_requests_alternative = [('responseSize', 'clientResponseSize', 'producerResponseSize'),
                                                    ('requestSize', 'clientRequestSize', 'producerRequestSize')]

example_request_limit = 10  # 0 means no limit

# FILTERING

accepted_date_formats = ["%a %Y-%m-%d %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"]

incident_expiration_time = 14400  # minutes
