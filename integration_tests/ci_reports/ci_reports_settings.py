import logging
import os
from logging import FileHandler


class Settings:
    THREAD_COUNT = 4

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
    # MongoDB configuration
    # --------------------------------------------------------
    MONGODB_USER = "ci_test"
    MONGODB_PWD = "ci_test"
    MONGODB_SERVER = "opmon.ci.kit"
    MONGODB_SUFFIX = "PY-INTEGRATION-TEST"

    CORRECTOR_ID = 'reports_{0}'.format(MONGODB_SUFFIX)

    # --------------------------------------------------------
    # Configure logger
    # --------------------------------------------------------
    LOGGER_NAME = 'reports_module'
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
    HEARTBEAT_NAME = 'CI_heartbeat_reports.json'
