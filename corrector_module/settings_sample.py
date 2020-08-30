import logging
import os
from logging.handlers import WatchedFileHandler


# --------------------------------------------------------
# Settings
# --------------------------------------------------------
class Settings:
    # --------------------------------------------------------
    # General settings
    # --------------------------------------------------------
    MODULE = "corrector"
    APPDIR = "/srv/app"
    INSTANCE = "sample"

    # --------------------------------------------------------
    # MongoDB settings
    # --------------------------------------------------------
    MONGODB_USER = '{0}_{1}'.format(MODULE, INSTANCE)
    MONGODB_PWD = "#NA"
    MONGODB_SERVER = "#NA"
    MONGODB_SUFFIX = '{0}'.format(INSTANCE)
    MONGODB_DATABASE = 'query_db_{0}'.format(INSTANCE)

    CORRECTOR_ID = '{0}'.format(MONGODB_USER)

    # --------------------------------------------------------
    # Module settings
    # --------------------------------------------------------
    CORRECTOR_DOCUMENTS_LIMIT = 20000
    CORRECTOR_TIMEOUT_DAYS = 3

    # Time to wait from process error, in seconds
    WAIT_FROM_ERROR = 600
    # Time to wait from process done with few documents, in seconds
    WAIT_FROM_DONE = 300
    # If number of processed docs is smaller than CORRECTOR_DOCUMENTS_MIN,
    # waits WAIT_FROM_DONE to restart batch
    # CORRECTOR_DOCUMENTS_MIN = 1
    CORRECTOR_DOCUMENTS_MIN = CORRECTOR_DOCUMENTS_LIMIT
    # Match THREAD_COUNT with number of cores * CPUs available to ensure best performance
    THREAD_COUNT = 8

    # Time window to match documents (in milliseconds)
    # TIME_WINDOW = 1 * 60 * 1000
    TIME_WINDOW = 10 * 60 * 1000

    CALC_TOTAL_DURATION = True
    CALC_CLIENT_SS_REQUEST_DURATION = True
    CALC_CLIENT_SS_RESPONSE_DURATION = True
    CALC_PRODUCER_DURATION_CLIENT_VIEW = True
    CALC_PRODUCER_DURATION_PRODUCER_VIEW = True
    CALC_PRODUCER_SS_REQUEST_DURATION = True
    CALC_PRODUCER_SS_RESPONSE_DURATION = True
    CALC_PRODUCER_IS_DURATION = True
    CALC_REQUEST_NW_DURATION = True
    CALC_RESPONSE_NW_DURATION = True
    CALC_REQUEST_SIZE = True
    CALC_RESPONSE_SIZE = True

    COMPARISON_LIST = ['clientMemberClass', 'requestMimeSize', 'serviceSubsystemCode', 'requestAttachmentCount',
                       'serviceSecurityServerAddress', 'messageProtocolVersion', 'responseSoapSize', 'succeeded',
                       'clientSubsystemCode', 'responseAttachmentCount', 'serviceMemberClass', 'messageUserId',
                       'serviceMemberCode', 'serviceXRoadInstance', 'clientSecurityServerAddress', 'clientMemberCode',
                       'clientXRoadInstance', 'messageIssue', 'serviceVersion', 'requestSoapSize', 'serviceCode',
                       'representedPartyClass', 'representedPartyCode', 'soapFaultCode', 'soapFaultString',
                       'responseMimeSize', 'messageId']

    comparison_list_orphan = [
        'clientMemberClass', 'serviceSubsystemCode', 'serviceSecurityServerAddress', 'messageProtocolVersion',
        'succeeded',
        'clientSubsystemCode', 'serviceMemberClass', 'messageUserId', 'serviceMemberCode', 'serviceXRoadInstance',
        'clientSecurityServerAddress', 'clientMemberCode', 'clientXRoadInstance', 'messageIssue', 'serviceVersion',
        'serviceCode', 'representedPartyClass', 'representedPartyCode', 'soapFaultCode', 'soapFaultString', 'messageId'
    ]

    # --------------------------------------------------------
    # Logger settings
    # --------------------------------------------------------
    LOGGER_PATH = '{0}/{1}/logs/'.format(APPDIR, INSTANCE)
    LOGGER_NAME = '{0}'.format(MODULE)
    # LOGGER_FILE = 'log_{0}_{1}.json'.format(MODULE, INSTANCE)

    logger = logging.getLogger(LOGGER_NAME)

    # INFO - logs INFO & WARNING & ERROR
    # WARNING - logs WARNING & ERROR
    # ERROR - logs ERROR
    logger.setLevel(logging.INFO)
    log_file_name = 'log_{0}_{1}.json'.format(MODULE, INSTANCE)
    log_file = os.path.join(LOGGER_PATH, log_file_name)
    formatter = logging.Formatter("%(message)s")
    file_handler = WatchedFileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # --------------------------------------------------------
    # Heartbeat settings
    # --------------------------------------------------------
    HEARTBEAT_LOGGER_PATH = '{0}/{1}/heartbeat/'.format(APPDIR, INSTANCE)
    HEARTBEAT_FILE = 'heartbeat_{0}_{1}.json'.format(MODULE, INSTANCE)

# --------------------------------------------------------
# End of settings
# --------------------------------------------------------
