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

import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from logging import Logger
from typing import Dict, Optional, Sequence, TypedDict

import requests


class MemberCountData(TypedDict):
    class_name: str
    description: str
    count: int


class MemberInConfig(TypedDict):
    class_name: str
    description: Optional[str]


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

    def get_members_in_config(self) -> Sequence[MemberInConfig]:
        try:
            shared_params = self._get_shared_params()
            return self._parse_memebers_in_config(shared_params)
        except Exception as e:
            self.logger.exception(f'CentralServerClient.get_members_in_config: {repr(e)}')
            raise e

    def get_member_count(self, members_in_config: Sequence[MemberInConfig]) -> Sequence[MemberCountData]:
        members_list = self.get_members()
        unique_counts: Dict[str, set] = {}

        for member_in_config in members_in_config:
            member_class = member_in_config['class_name']
            unique_counts[member_class.lower()] = set()

        for member in members_list:
            member_class = member['member_class']
            member_code = member['member_code']

            member_count_set = unique_counts.get(member_class.lower())
            if member_code and member_count_set is not None:
                if member_code not in member_count_set:
                    unique_counts[member_class.lower()].add(member_code)

        members_counts = [
            MemberCountData(
                class_name=member['class_name'],
                description=member['description'] or '',
                count=len(unique_counts[member['class_name'].lower()])
            )
            for member in members_in_config
        ]
        return members_counts

    @lru_cache(maxsize=1)
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

    @staticmethod
    def _parse_memebers_in_config(shared_params: requests.Response) -> Sequence[MemberInConfig]:
        global_members = []
        root = ET.fromstring(shared_params.content)
        for member in root.findall('./globalSettings/memberClass'):
            if member is None:
                continue
            member_code = member.find('./code')
            if member_code is None or member_code.text is None:
                continue
            member_description = member.find('./description')
            global_members.append(
                MemberInConfig(
                    class_name=member_code.text,
                    description=member_description.text if member_description is not None else ''
                )
            )
        return global_members
