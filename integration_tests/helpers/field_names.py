
# From RIA
string_fields = [
    'securityServerInternalIp',
    'securityServerType',
    'clientXRoadInstance',
    'clientMemberClass',
    'clientMemberCode',
    'clientSubsystemCode',
    'serviceXRoadInstance',
    'serviceMemberClass',
    'serviceMemberCode',
    'serviceSubsystemCode',
    'serviceCode',
    'serviceVersion',
    'representedPartyClass',
    'representedPartyCode',
    'messageId',
    'messageUserId',
    'messageIssue',
    'messageProtocolVersion',
    'clientSecurityServerAddress',
    'serviceSecurityServerAddress',
    'soapFaultCode',
    'soapFaultString'
]

# Minimum value 0
integer_fields = [
    'monitoringDataTs',
    'requestInTs',
    'requestOutTs',
    'responseInTs',
    'responseOutTs',
    'requestSoapSize',
    'requestMimeSize',
    'requestAttachmentCount',
    'responseSoapSize',
    'responseMimeSize',
    'responseAttachmentCount'
]

boolean_fields = ['succeeded']

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
