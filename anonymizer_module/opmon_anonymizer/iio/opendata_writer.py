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

import os
import yaml

from .postgresql_manager import PostgreSqlManager

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


class OpenDataWriter(object):

    def __init__(self, settings, logger):
        self._settings = settings

        field_data_path = settings['anonymizer']['field-data-file']
        if not field_data_path.startswith('/'):
            field_data_path = os.path.join(ROOT_DIR, '..', 'cfg_lists', field_data_path)

        schema, index_columns = self._get_schema(field_data_path)

        self.db_manager = PostgreSqlManager(settings['postgres'], schema, index_columns, logger)

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
            index_columns = []

            for field_name, field_data in yaml.safe_load(field_data_file)['fields'].items():
                if field_name not in ['id']:
                    schema.append((field_name, field_data['type']))
                    if field_data.get('index'):
                        index_columns.append(field_name)

            schema.sort()

        return schema, index_columns
