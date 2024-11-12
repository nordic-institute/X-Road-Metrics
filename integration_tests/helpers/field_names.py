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
