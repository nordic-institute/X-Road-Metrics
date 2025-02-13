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

import json
from json import JSONDecodeError
from typing import List

import jsonschema
from jsonschema import ValidationError

from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .reports_arguments import OpmonReportsArguments
from .xroad_descriptor_schema import xroad_descriptor_schema


class OpmonXroadDescriptor:
    """
    This class is used to hold all X-Road subsystems that the X-Road Metrics Reports module should target.
    The subsystem list can be retrieved from an xroad-descriptor.json file or constructed from xroad-metrics database.
    If user has specified a target subsystem as commandline argument then only that single subsystem is included in
    the descriptor.
    """
    def __init__(self, reports_arguments: OpmonReportsArguments, database: DatabaseManager, logger: LoggerManager):
        self.path = reports_arguments.settings['xroad'].get('descriptor-path')
        self.subsystem_from_arguments = reports_arguments.subsystem
        self.database = database
        self.logger = logger
        self._data: List[dict] = []

        self._parse_descriptor_file()
        self._process_subsystem_from_arguments()

        if not self._data:
            self._get_subsystems_from_database(
                reports_arguments.start_time_milliseconds,
                reports_arguments.end_time_milliseconds
            )

    def __getitem__(self, index):
        return OpmonXroadSubsystemDescriptor(self._data[index])

    def __iter__(self):
        for subsystem_data in self._data:
            yield OpmonXroadSubsystemDescriptor(subsystem_data)

    def __len__(self):
        return len(self._data)

    def _find(self, subsystem_to_find: dict):
        return next((subsystem for subsystem in self._data if self._compare(subsystem, subsystem_to_find)), {})

    @staticmethod
    def _compare(subsystem1: dict, subsystem2: dict):
        keys = ['x_road_instance', 'member_class', 'member_code', 'subsystem_code']
        return {key: subsystem1.get(key) for key in keys} == {key: subsystem2.get(key) for key in keys}

    def _handle_missing_file(self, e):
        if self.subsystem_from_arguments:
            self.logger.log_warning(
                "OpmonXroadDescriptor",
                f"X-Road descriptor file {self.path} not found. Proceeding without detailed descriptions."
            )
            return

        self.logger.log_error(
            "OpmonXroadDescriptor",
            f"X-Road descriptor file {self.path} not found but it is defined in the settings. Aborting."
        )
        raise e

    def _handle_parsing_error(self, e):
        if self.subsystem_from_arguments:
            self.logger.log_warning(
                "OpmonXroadDescriptor",
                f"X-Road descriptor file {self.path} parsing failed. Proceeding without detailed descriptions."
            )
            return

        self.logger.log_error(
            "OpmonXroadDescriptor",
            f"X-Road descriptor file {self.path} parsing failed. Check the file syntax. Aborting. Details: {e}"
        )
        raise e

    def _parse_descriptor_file(self):
        if not self.path:
            self.logger.log_info('OpmonXroadDescriptor', 'X-Road Descriptor file not specified.')
            return

        self.logger.log_info('OpmonXroadDescriptor', 'Start parsing info file.')
        try:
            with open(self.path, 'r') as f:
                json_data = f.read()
                self._data = json.loads(json_data)
                jsonschema.validate(instance=self._data, schema=xroad_descriptor_schema)
        except FileNotFoundError as e:
            self._handle_missing_file(e)
        except (ValidationError, JSONDecodeError) as e:
            self._handle_parsing_error(e)

    def _process_subsystem_from_arguments(self):
        # If a subsystem was specified on command line, then only that subsystem is included in the descriptor.
        if self.subsystem_from_arguments is not None:
            subsystem_descriptor = self._find(self.subsystem_from_arguments)
            self._data = [subsystem_descriptor] if subsystem_descriptor != {} else [self.subsystem_from_arguments]

    def _get_subsystems_from_database(self, start_time, end_time):
        self.logger.log_info('OpmonXroadDescriptor', 'Fetching subsystem list from database.')
        self._data = self.database.get_unique_subsystems(start_time, end_time)


class OpmonXroadSubsystemDescriptor:
    def __init__(self, subsystem_data: dict):
        self._data = subsystem_data

    @property
    def xroad_instance(self):
        return self._data['x_road_instance']

    @property
    def member_class(self):
        return self._data['member_class']

    @property
    def member_code(self):
        return self._data['member_code']

    @property
    def subsystem_code(self):
        return self._data['subsystem_code']

    def get_subsystem_name(self, language: str):
        subsystem_names = self._data.get('subsystem_name') or {}
        return subsystem_names.get(language) or self.subsystem_code

    def get_member_name(self):
        return self._data.get('member_name') or self.member_code

    def get_emails(self):
        return self._data.get('email') or []
