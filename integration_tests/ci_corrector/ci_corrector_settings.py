import logging
from logging import FileHandler
import os


class Settings:

    CORRECTOR_DOCUMENTS_LIMIT = 20000
    CORRECTOR_TIMEOUT_DAYS = 10

    THREAD_COUNT = 4

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
        'clientMemberClass', 'serviceSubsystemCode', 'serviceSecurityServerAddress', 'messageProtocolVersion', 'succeeded',
        'clientSubsystemCode', 'serviceMemberClass', 'messageUserId', 'serviceMemberCode', 'serviceXRoadInstance',
        'clientSecurityServerAddress', 'clientMemberCode', 'clientXRoadInstance', 'messageIssue', 'serviceVersion',
        'serviceCode', 'representedPartyClass', 'representedPartyCode', 'soapFaultCode', 'soapFaultString', 'messageId'
    ]

    # --------------------------------------------------------
    # MongoDB configuration
    # --------------------------------------------------------
    MONGODB_USER = "ci_test"
    MONGODB_PWD = "ci_test"
    MONGODB_SERVER = "opmon.ci.kit"
    MONGODB_SUFFIX = "PY-INTEGRATION-TEST"
    MONGODB_DATABASE = 'CI_query_db'

    CORRECTOR_ID = 'corrector_{0}'.format(MONGODB_SUFFIX)

    # --------------------------------------------------------
    # Configure logger
    # --------------------------------------------------------
    LOGGER_NAME = 'corrector_module'
    LOGGER_PATH = './integration_tests/logs/'
    logger = logging.getLogger(LOGGER_NAME)
    LOGGER__MAX_SIZE = 2 * 1024 * 1024
    LOGGER_BACKUP_COUNT = 10

    # INFO - logs INFO & WARNING & ERROR
    # WARNING - logs WARNING & ERROR
    # ERROR - logs ERROR
    logger.setLevel(logging.INFO)
    log_file_name = 'CI_{0}.json'.format(LOGGER_NAME)
    formatter = logging.Formatter("%(message)s")
    rotate_handler = FileHandler(os.path.join(LOGGER_PATH, log_file_name))
    rotate_handler.setFormatter(formatter)
    logger.addHandler(rotate_handler)

    # --------------------------------------------------------
    # Configure heartbeat
    # --------------------------------------------------------
    HEARTBEAT_LOGGER_PATH = './integration_tests/heartbeat/'
    HEARTBEAT_NAME = 'CI_heartbeat_corrector.json'
