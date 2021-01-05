# --------------------------------------------------------
# Report constants
# --------------------------------------------------------
# The column order for produced services
PRODUCED_SERVICES_COLUMN_ORDER = ["SERVICE", "CLIENT", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]
# The column order for consumed services
CONSUMED_SERVICES_COLUMN_ORDER = ["PRODUCER", "SERVICE", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]
# Sort the report rows by the following columns
PRODUCED_SERVICES_SORTING_ORDER = ["SERVICE", "CLIENT"]
CONSUMED_SERVICES_SORTING_ORDER = ["PRODUCER", "SERVICE"]
# Group the report rows by the following columns
PRODUCED_SERVICES_GROUPING_ORDER = ["SERVICE", "CLIENT"]
CONSUMED_SERVICES_GROUPING_ORDER = ["PRODUCER", "SERVICE"]
# The list of services that are considered as meta services
META_SERVICE_LIST = ["getWsdl", "listMethods", "allowedMethods", "getSecurityServerMetrics",
                     "getSecurityServerOperationalData", "getSecurityServerHealthData",
                     "getOpenAPI"]
# The following producer fields are merged
PRODUCER_MERGED_FIELDS_1 = (["serviceCode", "serviceVersion"], ".", "service")
PRODUCER_MERGED_FIELDS_2 = (
    ["clientXRoadInstance", "clientMemberClass", "clientMemberCode", "clientSubsystemCode"], "/", "client")
# The following consumer fields are merged
CONSUMER_MERGED_FIELDS_1 = (["serviceCode", "serviceVersion"], ".", "service")
CONSUMER_MERGED_FIELDS_2 = (
    ["serviceXRoadInstance", "serviceMemberClass", "serviceMemberCode", "serviceSubsystemCode"], "/", "producer")
HTML_TEMPLATE_PATH = "/reports_module/pdf_files/pdf_report_template.html"
CSS_FILES = ["reports_module/pdf_files/pdf_report_style.css"]
# Load RIA images
RIA_IMAGE_1 = "reports_module/pdf_files/header_images/ria_75_{LANGUAGE}.png"
RIA_IMAGE_2 = "reports_module/pdf_files/header_images/eu_rdf_75_{LANGUAGE}.png"
RIA_IMAGE_3 = "reports_module/pdf_files/header_images/xroad_75_{LANGUAGE}.png"
# Translations
TRANSLATION_FILES = 'reports_module/lang/{LANGUAGE}_lang.json'
