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
from logging import Logger
from typing import Dict, Sequence, TypedDict

import requests


class MemberCountData(TypedDict):
    member_gov_count: int
    member_com_count: int
    member_org_count: int


class MemberData(TypedDict):
    member_class: str
    member_code: str


class CentralServerClient:
    def __init__(self, xroad_settings: dict, logger: Logger):
        self.url = f"{xroad_settings['central-server']['protocol']}{xroad_settings['central-server']['host']}"
        self.timeout = xroad_settings['central-server']['timeout']
        self.logger = logger

    def get_members(self) -> Sequence[MemberData]:
        try:
            shared_params = self._get_shared_params()
            return self._parse_members_list(shared_params)
        except Exception as e:
            self.logger.exception(f'CentralServerClient.get_members: {repr(e)}')
            raise e

    def get_member_count(self) -> MemberCountData:
        members_list = self.get_members()
        unique_counts: Dict[str, set] = {}

        for member in members_list:
            member_class = member['member_class']
            member_code = member['member_code']
            member_count_key = f'member_{member_class.lower()}_count'

            if member_count_key not in unique_counts:
                unique_counts[member_count_key] = set()

            if member_code:
                unique_counts[member_count_key].add(member_code)
        members_count: MemberCountData = {
            'member_gov_count': len(unique_counts['member_gov_count']),
            'member_com_count': len(unique_counts['member_com_count']),
            'member_org_count': len(unique_counts['member_org_count'])
        }
        return members_count

    def _get_shared_params(self) -> requests.Response:
        internal_conf_url = f'{self.url}/internalconf'

        global_conf = requests.get(internal_conf_url, timeout=self.timeout)
        global_conf.raise_for_status()
        #  NB! re.search global configuration regex might be changed
        # according version naming or other future naming conventions
        data = global_conf.content.decode('utf-8')
        s = re.search(r'Content-location: (/V\d+/\d+/shared-params.xml)', data)
        if s is None:
            raise ValueError('Pattern was not found in data')
        shared_params = requests.get(f'{self.url}{s.group(1)}', timeout=self.timeout)
        shared_params.raise_for_status()
        return shared_params

    @staticmethod
    def _parse_members_list(shared_params: requests.Response) -> Sequence[MemberData]:
        members_list = []

        root = ET.fromstring(shared_params.content)
        for server in root.findall('./securityServer'):
            if server is None:
                continue
            owner_id = server.find('./owner')
            if owner_id is None:
                continue
            owner = root.find("./member[@id='{0}']".format(owner_id.text))
            if owner is None:
                continue

            member_class = owner.find('./memberClass/code')
            member_code = owner.find('./memberCode')

            if member_class is None or not member_class.text:
                continue

            if member_code is None or not member_code.text:
                continue

            member_data: MemberData = {
                'member_class': member_class.text,
                'member_code': member_code.text,
            }

            members_list.append(member_data)
        return members_list
