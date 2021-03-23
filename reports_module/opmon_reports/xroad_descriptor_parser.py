import json
from json import JSONDecodeError

import jsonschema
from jsonschema import ValidationError

from .reports_arguments import OpmonReportsArguments
from .xroad_descriptor_schema import xroad_descriptor_schema


class OpmonXroadDescriptor:
    def __init__(self, info_file_path, logger):
        logger.log_info('OpmonSubsystemInfo', 'Start parsing info file.')

        self.path = info_file_path
        self.logger = logger

        self._data = []
        try:
            with open(info_file_path, 'r') as f:
                json_data = f.read()
            self._data = json.loads(json_data)
            jsonschema.validate(instance=self._data, schema=xroad_descriptor_schema)
        except FileNotFoundError:
            self._handle_missing_file()
        except (ValidationError, JSONDecodeError) as e:
            self._handle_parsing_error(e)

    def get_subsystem_name(self, reports_args: OpmonReportsArguments):
        descriptor = self._find(reports_args)
        subsystem_names = descriptor.get('subsystem_name') or {}
        return subsystem_names.get(reports_args.language) or reports_args.subsystem_code

    def get_member_name(self, reports_args: OpmonReportsArguments):
        descriptor = self._find(reports_args)
        return descriptor.get('member_name') or reports_args.member_code

    def get_emails(self, reports_args: OpmonReportsArguments):
        descriptor = self._find(reports_args)
        return descriptor.get('email') or []

    def _find(self, reports_args: OpmonReportsArguments):
        return next((subsystem for subsystem in self._data if self._compare(subsystem, reports_args)), {})

    @staticmethod
    def _compare(subsystem: dict, reports_args: OpmonReportsArguments):
        return subsystem['member_code'] == reports_args.member_code \
            and subsystem['subsystem_code'] == reports_args.subsystem_code \
            and subsystem['member_class'] == reports_args.member_class \
            and subsystem['x_road_instance'] == reports_args.xroad_instance

    def _handle_missing_file(self):
        self.logger.log_warning(
            "OpmonSubsystemInfo",
            f"The info file {self.path} not found. Using default placeholders."
        )

    def _handle_parsing_error(self, e):
        self.logger.log_warning(
            "OpmonSubsystemInfo",
            f"Info file {self.path} parsing failed. Using default placeholders. Details: {e}"
        )
        self._data = []
