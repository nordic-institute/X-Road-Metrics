#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#
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
