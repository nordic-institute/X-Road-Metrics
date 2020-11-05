import re
import requests
import xml.etree.ElementTree as ET


class CentralServerClient:
    def __init__(self, xroad_settings, logger_m):
        self.url = f"{xroad_settings['central-server']['protocol']}{xroad_settings['central-server']['host']}"
        self.logger_m = logger_m

    def get_security_servers(self):
        server_list = []

        timeout = self.xroad_cs['timeout']
        # Downloading shared-params.xml
        try:
            internal_conf_url = f"{self.url}/internalconf"
            global_conf = requests.get(internal_conf_url, timeout=timeout)
            global_conf.raise_for_status()
            #  NB! re.search global configuration regex might be changed
            # according version naming or other future naming conventions
            data = global_conf.content.decode("utf-8")
            s = re.search(r"Content-location: (/V\d+/\d+/shared-params.xml)", data)
            shared_params = requests.get(f"{self.url}{s.group(1)}", timeout=timeout)
            shared_params.raise_for_status()
        except Exception as e:
            self.logger_m.log_warning('ServerManager.get_list_from_central_server', f'{repr(e)}')
            return []

        try:
            root = ET.fromstring(shared_params.content)
            instance = root.find("./instanceIdentifier").text
            for server in root.findall("./securityServer"):
                ownerId = server.find("./owner").text
                owner = root.find("./member[@id='{0}']".format(ownerId))
                memberClass = owner.find("./memberClass/code").text
                memberCode = owner.find("./memberCode").text
                serverCode = server.find("./serverCode").text
                address = server.find("./address").text
                s = instance + "/" + memberClass + "/" + memberCode + "/" + serverCode + "/" + address
                data = {}
                data['ownerId'] = ownerId
                data['instance'] = instance
                data['memberClass'] = memberClass
                data['memberCode'] = memberCode
                data['serverCode'] = serverCode
                data['address'] = address
                data['server'] = s
                server_list.append(data)

        except Exception as e:
            self.logger_m.log_warning('ServerManager.get_list_from_central_server', '{0}'.format(repr(e)))
            return []

        return server_list

