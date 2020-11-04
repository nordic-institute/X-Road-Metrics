""" Database Manager - Collector Module
"""

import time
import re
import requests
import xml.etree.ElementTree as ET

import pymongo


class DatabaseManager:

    def __init__(self, mongo_settings, xroad_settings, logger_manager):
        xroad_instance = xroad_settings['instance']
        self.xroad_cs = xroad_settings['central-server']
        self.mongo_uri = \
            f"mongodb://{mongo_settings['user']}:{mongo_settings['password']}@{mongo_settings['host']}/auth_db"
        self.db_name = f'query_db_{xroad_instance}'
        self.db_collector_state = f'collector_state_{xroad_instance}'
        self.collector_id = f'collector_{xroad_instance}'
        self.logger_m = logger_manager

    @staticmethod
    def get_timestamp():
        return float(time.time())

    def get_list_from_central_server(self):
        server_list = []
        cs_url = f"{self.xroad_cs['protocol']}{self.xroad_cs['host']}"
        timeout = self.xroad_cs['timeout']
        # Downloading shared-params.xml
        try:
            internal_conf_url = f"{cs_url}/internalconf"
            globalConf = requests.get(internal_conf_url, timeout=timeout)
            globalConf.raise_for_status()
            #  NB! re.search global configuration regex might be changed
            # according version naming or other future naming conventions
            data = globalConf.content.decode("utf-8")
            s = re.search(r"Content-location: (/V\d+/\d+/shared-params.xml)", data)
            sharedParams = requests.get(f"{cs_url}{s.group(1)}", timeout=timeout)
            sharedParams.raise_for_status()
        except Exception as e:
            self.logger_m.log_warning('ServerManager.get_list_from_central_server', f'{repr(e)}')
            return []

        try:
            root = ET.fromstring(sharedParams.content)
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

    def save_server_list_to_database(self, server_list):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            collection = db['server_list']
            data = dict()
            data['timestamp'] = self.get_timestamp()
            data['server_list'] = server_list
            data['collector_id'] = self.collector_id
            collection.insert(data)
        except Exception as e:
            self.logger_m.log_error('ServerManager.get_server_list_database', '{0}'.format(repr(e)))
            raise e

    def get_server_list_from_database(self):
        """
        Get the most recent server list from MongoDB
        """
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            data = db['server_list'].find({'collector_id': self.collector_id}).sort([('timestamp', -1)]).limit(1)[0]
            return data['server_list'], data['timestamp']
        except Exception as e:
            self.logger_m.log_error('ServerManager.get_server_list_database', '{0}'.format(repr(e)))
            raise e

    def get_next_records_timestamp(self, server_key, records_from_offset):
        """ Returns next records_from pointer for the given server
        """
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            collection = db['collector_pointer']
            cur = collection.find_one({'server': server_key})
            if cur is None:
                # If server not in MongoDB
                data = dict()
                data['server'] = server_key
                data['records_from'] = self.get_timestamp() - records_from_offset
                collection.insert(data)
            else:
                data = cur
            # Return pointers
            records_from = data['records_from']
        except Exception as e:
            self.logger_m.log_error('ServerManager.get_next_records_timestamp', '{0}'.format(repr(e)))
            raise e
        return records_from

    def set_next_records_timestamp(self, server_key, records_from):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            collection = db['collector_pointer']
            data = dict()
            data['server'] = server_key
            data['records_from'] = records_from
            collection.find_and_modify(query={'server': server_key},
                                       update=data, upsert=True)
        except Exception as e:
            self.logger_m.log_error('ServerManager.set_next_records_timestamp', '{0}'.format(repr(e)))
            raise e

    def insert_data_to_raw_messages(self, data_list):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_name]
            raw_msg = db['raw_messages']
            # Add timestamp to data list
            for data in data_list:
                timestamp = self.get_timestamp()
                data['insertTime'] = timestamp
            # Save all
            raw_msg.insert_many(data_list)
        except Exception as e:
            self.logger_m.log_error('ServerManager.insert_data_to_raw_messages', '{0}'.format(repr(e)))
            raise e

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
