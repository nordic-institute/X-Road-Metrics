
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

    LOGGER_NAME = "test"

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
