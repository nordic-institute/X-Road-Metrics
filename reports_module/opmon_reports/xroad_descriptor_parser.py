import json
from json import JSONDecodeError

import jsonschema
from jsonschema import ValidationError

from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .reports_arguments import OpmonReportsArguments
from .xroad_descriptor_schema import xroad_descriptor_schema


class OpmonXroadDescriptor:
    def __init__(self, reports_arguments: OpmonReportsArguments, database: DatabaseManager, logger: LoggerManager):
        self.path = reports_arguments.settings['xroad']['descriptor-path']
        self.database = database
        self.logger = logger
        self._data = []

        self._parse_descriptor_file()
        self._process_subsystem_argument(reports_arguments)

        if not self._data:
            self._get_subsystems_from_database(reports_arguments)

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

    def _handle_missing_file(self):
        self.logger.log_warning(
            "OpmonXroadDescriptor",
            f"The info file {self.path} not found. Using default placeholders."
        )

    def _handle_parsing_error(self, e):
        self.logger.log_warning(
            "OpmonXroadDescriptor",
            f"Info file {self.path} parsing failed. Using default placeholders. Details: {e}"
        )
        self._data = []

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
        except FileNotFoundError:
            self._handle_missing_file()
        except (ValidationError, JSONDecodeError) as e:
            self._handle_parsing_error(e)

    def _process_subsystem_argument(self, args):
        # If a subsystem was specified on command line, then only that subsystem is included in the descriptor.
        if args.subsystem is not None:
            subsystem_descriptor = self._find(args.subsystem)
            self._data = [subsystem_descriptor] if subsystem_descriptor != {} else [args.subsystem]

    def _get_subsystems_from_database(self, reports_arguments):
        self.logger.log_info('OpmonXroadDescriptor', 'Fetching subsystem list from database.')
        self._data = self.database.get_unique_subsystems(
            reports_arguments.start_time_milliseconds,
            reports_arguments.end_time_milliseconds
        )


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
