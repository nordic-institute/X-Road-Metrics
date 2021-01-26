import os
import yaml

from .postgresql_manager import PostgreSQL_Manager

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


class OpenDataWriter(object):

    def __init__(self, settings, logger):
        self._settings = settings

        field_data_path = settings['anonymizer']['field-data-file']
        if not field_data_path.startswith('/'):
            field_data_path = os.path.join(ROOT_DIR, '..', 'cfg_lists', field_data_path)

        schema = self._get_schema(field_data_path)

        self.db_manager = PostgreSQL_Manager(settings['postgres'], schema, logger)

    def write_records(self, records):
        self.db_manager.add_data(records)

    @staticmethod
    def _ensure_directory(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def _get_schema(field_data_file_path):
        with open(field_data_file_path) as field_data_file:
            schema = []

            for field_name, field_data in yaml.safe_load(field_data_file)['fields'].items():
                if field_name not in ['id']:
                    schema.append((field_name, field_data['type']))

            schema.sort()

        return schema
