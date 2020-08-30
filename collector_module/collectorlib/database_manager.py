""" Database Manager - Collector Module
"""

import time
import re
import requests
import xml.etree.ElementTree as ET

import pymongo


RAW_DATA_COLLECTION = 'raw_messages'


class DatabaseManager:

    def __init__(self, mdb_suffix, mongodb_server, mongodb_user, mongodb_pwd, logger_manager):
        self.mdb_server = mongodb_server
        self.mdb_user = mongodb_user
        self.mdb_pwd = mongodb_pwd
        self.db_name = 'query_db_{0}'.format(mdb_suffix)
        self.db_collector_state = 'collector_state_{0}'.format(mdb_suffix)
        self.collector_id = 'collector_{0}'.format(mdb_suffix)
        self.logger_m = logger_manager

    @staticmethod
    def get_timestamp():
        return float(time.time())

    def get_list_from_central_server(self, central_server, timeout):
        server_list = []
        # Downloading shared-params.xml
        try:
            url_str = "http://{0}/internalconf".format(central_server)
            globalConf = requests.get(url_str, timeout=timeout)
            globalConf.raise_for_status()
            #  NB! re.search global configuration regex might be changed
            # according version naming or other future naming conventions
            data = globalConf.content.decode("utf-8")
            s = re.search(r"Content-location: (/V\d+/\d+/shared-params.xml)", data)
            sharedParams = requests.get("http://{0}{1}".format(central_server, s.group(1)), timeout=timeout)
            sharedParams.raise_for_status()
        except Exception as e:
            self.logger_m.log_warning('ServerManager.get_list_from_central_server', '{0}'.format(repr(e)))
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

    def stores_server_list_database(self, server_list):
        try:
            uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
            client = pymongo.MongoClient(uri)
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

    def get_server_list_database(self, n=1):
        """ Returns the top n most recent server list
        """
        try:
            uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
            client = pymongo.MongoClient(uri)
            db = client[self.db_collector_state]
            collection = db['server_list']
            cur = collection.find({'collector_id': self.collector_id}).sort([('timestamp', -1)]).limit(n)
        except Exception as e:
            self.logger_m.log_error('ServerManager.get_server_list_database', '{0}'.format(repr(e)))
            raise e
        return list(cur)

    def get_next_records_timestamp(self, server_key, records_from_offset):
        """ Returns next records_from pointer for the given server
        """
        try:
            uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
            client = pymongo.MongoClient(uri)
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
        uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
        try:
            client = pymongo.MongoClient(uri)
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
            uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
            client = pymongo.MongoClient(uri)
            db = client[self.db_name]
            raw_msg = db[RAW_DATA_COLLECTION]
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
    def get_soap_body(monitoring_client, xRoadInstance, memberClass, memberCode, serverCode, req_id, recordsFrom, recordsTo):
        body = """<SOAP-ENV:Envelope
               xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:id="http://x-road.eu/xsd/identifiers"
               xmlns:xrd="http://x-road.eu/xsd/xroad.xsd"
               xmlns:om="http://x-road.eu/xsd/op-monitoring.xsd">
            <SOAP-ENV:Header>
        """
        body += monitoring_client
        body += """<xrd:service id:objectType="SERVICE">
                    <id:xRoadInstance>""" + xRoadInstance + """</id:xRoadInstance>
                    <id:memberClass>""" + memberClass + """</id:memberClass>
                    <id:memberCode>""" + memberCode + """</id:memberCode>
                    <id:serviceCode>getSecurityServerOperationalData</id:serviceCode>
                </xrd:service>
                <xrd:securityServer id:objectType="SERVER">
                    <id:xRoadInstance>""" + xRoadInstance + """</id:xRoadInstance>
                    <id:memberClass>""" + memberClass + """</id:memberClass>
                    <id:memberCode>""" + memberCode + """</id:memberCode>
                    <id:serverCode>""" + serverCode + """</id:serverCode>
                </xrd:securityServer>
                <xrd:id>""" + req_id + """</xrd:id>
                <xrd:protocolVersion>4.0</xrd:protocolVersion>
            </SOAP-ENV:Header>
            <SOAP-ENV:Body>
                <om:getSecurityServerOperationalData>
                    <om:searchCriteria>
                        <om:recordsFrom>""" + str(recordsFrom) + """</om:recordsFrom>
                        <om:recordsTo>""" + str(recordsTo) + """</om:recordsTo>
                    </om:searchCriteria>
                </om:getSecurityServerOperationalData>
            </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>
        """
        return body
