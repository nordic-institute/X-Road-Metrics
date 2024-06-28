#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import re
import xml.etree.ElementTree as ET

import requests


class CentralServerClient:
    def __init__(self, xroad_settings, logger_m):
        central_server_settings = xroad_settings['central-server']
        self.url = f"{central_server_settings['protocol']}{central_server_settings['host']}"
        self.timeout = central_server_settings['timeout']
        self.server_cert = central_server_settings.get('tls-server-certificate')
        self.client_cert = (
            central_server_settings.get('tls-client-certificate'),
            central_server_settings.get('tls-client-key')
        )
        self.logger_m = logger_m

    def get_security_servers(self):
        try:
            shared_params = self._get_shared_params()
            return self._parse_server_list(shared_params)
        except Exception as e:
            self.logger_m.log_exception('CentralServerClient.get_security_servers', repr(e))
            raise e

    def _get_shared_params(self):
        internal_conf_url = f'{self.url}/internalconf'

        global_conf = requests.get(internal_conf_url, timeout=self.timeout, cert=self.client_cert,
                                   verify=self.server_cert)
        global_conf.raise_for_status()
        #  NB! re.search global configuration regex might be changed
        # according version naming or other future naming conventions
        data = global_conf.content.decode('utf-8')
        s = re.search(r'Content-location: (/V\d+/\d+/shared-params.xml)', data)
        shared_params = requests.get(f'{self.url}{s.group(1)}', timeout=self.timeout,
                                     cert=self.client_cert, verify=self.server_cert)
        shared_params.raise_for_status()
        return shared_params

    @staticmethod
    def _parse_server_list(shared_params):
        server_list = []

        root = ET.fromstring(shared_params.content)
        instance = root.find('./instanceIdentifier').text
        for server in root.findall('./securityServer'):
            owner_id = server.find('./owner').text
            owner = root.find("./member[@id='{0}']".format(owner_id))
            member_class = owner.find('./memberClass/code').text
            member_code = owner.find('./memberCode').text
            server_code = server.find('./serverCode').text
            address = server.find('./address').text
            server_str = instance + '/' + member_class + '/' + member_code + '/' + server_code + '/' + address

            server_data = {
                'ownerId': owner_id,
                'instance': instance,
                'memberClass': member_class,
                'memberCode': member_code,
                'serverCode': server_code,
                'address': address,
                'server': server_str
            }

            server_list.append(server_data)
        return server_list
