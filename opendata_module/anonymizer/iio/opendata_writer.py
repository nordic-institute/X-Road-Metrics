from datetime import datetime
import os
from collections import defaultdict
import os
import yaml

from .postgresql_manager import PostgreSQL_Manager

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


class OpenDataWriter(object):

    def __init__(self, config):
        self._config = config

        allowed_fields_file_path = (config.field_data_file if config.field_data_file.startswith('/') else
                                    os.path.join(ROOT_DIR, '..', 'cfg_lists', config.field_data_file))

        schema = self._get_schema(allowed_fields_file_path)

        db_data = {'host_address': config.postgres['host_address'],
                   'port_number': config.postgres['port'],
                   'database_name': config.postgres['database_name'],
                   'table_name': config.postgres['table_name'],
                   'user': config.postgres['user'],
                   'password': config.postgres['password'],
                   'table_schema': schema,
                   'readonly_users': config.postgres['readonly_users']}

        self._db_manager = PostgreSQL_Manager(**db_data)

    def write_records(self, records):
        self._db_manager.add_data(records)

    def _ensure_directory(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def _get_schema(self, field_data_file_path):
        with open(field_data_file_path) as field_data_file:
            schema = []

            for field_name, field_data in yaml.safe_load(field_data_file)['fields'].items():
                if field_name not in ['id']:
                    schema.append((field_name, field_data['type']))

            schema.sort()

        return schema
