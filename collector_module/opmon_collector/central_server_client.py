import re
import requests
import xml.etree.ElementTree as ET


class CentralServerClient:
    def __init__(self, xroad_settings, logger_m):
        self.url = f"{xroad_settings['central-server']['protocol']}{xroad_settings['central-server']['host']}"
        self.timeout = xroad_settings['central-server']['timeout']
        self.logger_m = logger_m

    def get_security_servers(self):
        try:
            shared_params = self._get_shared_params()
            return self._parse_server_list(shared_params)
        except Exception as e:
            self.logger_m.log_warning('CentralServerClient.get_security_servers', f'{repr(e)}')
            raise e
            #return []

    def _get_shared_params(self):
        internal_conf_url = f"{self.url}/internalconf"

        global_conf = requests.get(internal_conf_url, timeout=self.timeout)
        global_conf.raise_for_status()
        #  NB! re.search global configuration regex might be changed
        # according version naming or other future naming conventions
        data = global_conf.content.decode("utf-8")
        s = re.search(r"Content-location: (/V\d+/\d+/shared-params.xml)", data)
        shared_params = requests.get(f"{self.url}{s.group(1)}", timeout=self.timeout)
        shared_params.raise_for_status()
        return shared_params

    @staticmethod
    def _parse_server_list(shared_params):
        server_list = []

        root = ET.fromstring(shared_params.content)
        instance = root.find("./instanceIdentifier").text
        for server in root.findall("./securityServer"):

            owner_id = server.find("./owner").text
            owner = root.find("./member[@id='{0}']".format(owner_id))
            member_class = owner.find("./memberClass/code").text
            member_code = owner.find("./memberCode").text
            server_code = server.find("./serverCode").text
            address = server.find("./address").text
            server_str = instance + "/" + member_class + "/" + member_code + "/" + server_code + "/" + address

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
