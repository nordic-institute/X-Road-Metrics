import pytest
import os
import pathlib
import responses

from opmon_collector.central_server_client import CentralServerClient
from opmon_collector.settings import OpmonSettingsManager


@pytest.fixture
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@responses.activate
def test_get_security_servers(basic_settings, mocker):

    os.chdir(pathlib.Path(__file__).parent.absolute())
    with open('responses/shared-params.xml', "r") as f:
        shared_params = f.read()

    with open('responses/internalconf.txt', "r") as f:
        internal_conf_response = f.read()

    responses.add(responses.GET, 'http://x-road-cs/internalconf', body=internal_conf_response, status=200)
    responses.add(responses.GET, 'http://x-road-cs/V2/20201105104801222890000/shared-params.xml',
                  body=shared_params, status=200)

    client = CentralServerClient(basic_settings['xroad'], mocker.Mock())
    server_list = client.get_security_servers()

    expected_servers = [
        'DEV/ORG/1234567-8/ss1/x-road-ss',
        'DEV/ORG/1111111-1/ss2/x-road-ss-test'
    ]

    for expected in expected_servers:
        matches = [s for s in server_list if s['server'] == expected]
        assert len(matches) == 1

    for server in server_list:
        keys = set(server.keys())
        assert keys == {'ownerId', 'instance', 'memberClass', 'memberCode', 'serverCode', 'address', 'server'}
