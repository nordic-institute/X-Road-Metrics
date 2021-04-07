timestamp_field = 'requestInTs'

# These are present on the top level of "clean data" objects
top_level_column_names = [
    "_id",
    'totalDuration',
    'producerDurationProducerView',
    'requestNwDuration',
    'responseNwDuration',
    'correctorStatus'
]

# X-Road identifier column names
# These are present in both client and producer sections of clean data
service_identifier_column_names = [
    "clientMemberClass",
    "clientMemberCode",
    "clientXRoadInstance",
    "clientSubsystemCode",
    "serviceCode",
    "serviceVersion",
    "serviceMemberClass",
    "serviceMemberCode",
    "serviceXRoadInstance",
    "serviceSubsystemCode"
]

#  Request metadata columns in clean data client/producer sections
service_metadata_column_names = ["succeeded", "messageId", timestamp_field]
all_service_column_names = service_identifier_column_names + service_metadata_column_names

#  Alternative columns that are included primarily from client data and as a fallback from producer data.
alternative_columns = [
    {'outputName': 'requestSize', 'clientName': 'clientRequestSize', 'producerName': 'producerRequestSize'},
    {'outputName': 'responseSize', 'clientName': 'clientResponseSize', 'producerName': 'producerResponseSize'}
]
