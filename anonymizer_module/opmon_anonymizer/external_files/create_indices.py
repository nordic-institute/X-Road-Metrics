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

import logging
import os
import sys

import psycopg2 as pg
from settings import anonymizer, postgres  # type: ignore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

sys.path.append(os.path.join(ROOT_DIR, '..'))


def get_connection_string(
        host_address=None, port=None, database_name=None, user=None, password=None, **irrelevant_settings):
    string_parts = ['host={host} dbname={dbname}'.format(
        **{'host': host_address, 'dbname': database_name})]

    if port:
        string_parts.append('port=' + str(port))

    if user:
        string_parts.append('user=' + user)

    if password:
        string_parts.append('password=' + password)

    return ' '.join(string_parts)


connection_string = get_connection_string(**postgres)

if anonymizer['field_translations_file'].startswith('/'):
    field_translations_file_path = anonymizer['field_translations_file']
else:
    field_translations_file_path = os.path.join(ROOT_DIR, '../cfg_lists', anonymizer['field_translations_file'])

fields = set()
with open(field_translations_file_path) as field_translations_file:
    # fields = {line.strip().split(' -> ')[1].lower() for line in field_translations_file if line.strip()}
    fields.add('requestindate')

table_name = postgres['table_name']

for field_name in sorted(fields):
    try:
        with pg.connect(connection_string) as connection:
            cursor = connection.cursor()
            query = f'CREATE INDEX logs_{field_name}_idx ON {table_name} ({field_name});'
            cursor.execute(query)
            logger.info(f'Created index logs_{field_name}_idx with the command: {query}')

    except Exception as e:
        logger.exception(f'Create index query failed: {query}. Error: {str(e)}')
