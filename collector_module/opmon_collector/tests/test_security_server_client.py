from io import StringIO
import xml.etree.ElementTree as ET
from opmon_collector.security_server_client import SecurityServerClient


def test_get_soap_body():
    xroad_settings = {
        'instance': 'DEV',
        'monitoring-client': {
            'memberclass': 'testclass',
            'membercode': 'testcode',
            'subsystemcode': 'testsubcode'
        }
    }

    serverdata = {
        'instance': 'DEV',
        'memberClass': 'targetclass',
        'memberCode': 'targetcode',
        'serverCode': 'targetserver'
    }

    reqid = '123'
    recordsfrom = '12'
    recordsto = '34'

    client_xml = SecurityServerClient.get_soap_monitoring_client(xroad_settings)
    full_xml = SecurityServerClient.get_soap_body(
        client_xml,
        serverdata,
        reqid,
        recordsfrom,
        recordsto
    )

    root = _parse_xml_without_namespaces(full_xml)

    _assert_client_tag(root[0][0], xroad_settings)
    _assert_service_tag(root[0][1], xroad_settings, serverdata)
    _assert_server_tag(root[0][2], xroad_settings, serverdata)
    _assert_id_tag(root[0][3], reqid)
    _assert_search_criteria_tag(root[1][0][0], recordsfrom, recordsto)


def _assert_client_tag(client, xroad_settings):
    assert client.tag == 'client'
    assert client.find('xRoadInstance').text == xroad_settings['instance']
    assert client.find('memberClass').text == xroad_settings['monitoring-client']['memberclass']
    assert client.find('memberCode').text == xroad_settings['monitoring-client']['membercode']


def _assert_service_tag(service, xroad_settings, serverdata):
    assert service.tag == 'service'
    assert service.find('xRoadInstance').text == xroad_settings['instance']
    assert service.find('memberClass').text == serverdata['memberClass']
    assert service.find('memberCode').text == serverdata['memberCode']


def _assert_server_tag(server, xroad_settings, serverdata):
    assert server.tag == 'securityServer'
    assert server.find('xRoadInstance').text == xroad_settings['instance']
    assert server.find('memberClass').text == serverdata['memberClass']
    assert server.find('memberCode').text == serverdata['memberCode']
    assert server.find('serverCode').text == serverdata['serverCode']


def _assert_id_tag(id_tag, reqid):
    assert id_tag.tag == 'id'
    assert id_tag.text == reqid


def _assert_search_criteria_tag(search_criteria, recordsfrom, recordsto):
    assert search_criteria.tag == 'searchCriteria'
    assert search_criteria.find('recordsFrom').text == recordsfrom
    assert search_criteria.find('recordsTo').text == recordsto


def _parse_xml_without_namespaces(xml):
    it = ET.iterparse(StringIO(xml))
    for _, el in it:
        prefix, has_namespace, postfix = el.tag.partition('}')
        if has_namespace:
            el.tag = postfix
    return it.root