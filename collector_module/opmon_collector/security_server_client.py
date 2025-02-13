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

class SecurityServerClient:
    def __init__(self):
        pass

    @staticmethod
    def get_soap_body(client_xml, server_settings, req_id, records_from, records_to):
        body = """<SOAP-ENV:Envelope
                   xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:id="http://x-road.eu/xsd/identifiers"
                   xmlns:xrd="http://x-road.eu/xsd/xroad.xsd"
                   xmlns:om="http://x-road.eu/xsd/op-monitoring.xsd">
                <SOAP-ENV:Header>
            """
        body += client_xml
        body += """<xrd:service id:objectType="SERVICE">
                        <id:xRoadInstance>""" + server_settings['instance'] + """</id:xRoadInstance>
                        <id:memberClass>""" + server_settings['memberClass'] + """</id:memberClass>
                        <id:memberCode>""" + server_settings['memberCode'] + """</id:memberCode>
                        <id:serviceCode>getSecurityServerOperationalData</id:serviceCode>
                    </xrd:service>
                    <xrd:securityServer id:objectType="SERVER">
                        <id:xRoadInstance>""" + server_settings['instance'] + """</id:xRoadInstance>
                        <id:memberClass>""" + server_settings['memberClass'] + """</id:memberClass>
                        <id:memberCode>""" + server_settings['memberCode'] + """</id:memberCode>
                        <id:serverCode>""" + server_settings['serverCode'] + """</id:serverCode>
                    </xrd:securityServer>
                    <xrd:id>""" + req_id + """</xrd:id>
                    <xrd:protocolVersion>4.0</xrd:protocolVersion>
                </SOAP-ENV:Header>
                <SOAP-ENV:Body>
                    <om:getSecurityServerOperationalData>
                        <om:searchCriteria>
                            <om:recordsFrom>""" + str(records_from) + """</om:recordsFrom>
                            <om:recordsTo>""" + str(records_to) + """</om:recordsTo>
                        </om:searchCriteria>
                    </om:getSecurityServerOperationalData>
                </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>
            """
        return body

    @staticmethod
    def get_soap_monitoring_client(xroad_settings):
        client = xroad_settings['monitoring-client']
        return f"""
            <xrd:client id:objectType="SUBSYSTEM">
                <id:xRoadInstance>{xroad_settings['instance']}</id:xRoadInstance>
                <id:memberClass>{client['memberclass']}</id:memberClass>
                <id:memberCode>{client['membercode']}</id:memberCode>
                <id:subsystemCode>{client['subsystemcode']}</id:subsystemCode>
            </xrd:client>
            """
