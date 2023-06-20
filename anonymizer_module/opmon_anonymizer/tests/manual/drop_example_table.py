import logging
import os
import sys

import psycopg2 as pg
from settings import postgres  # type: ignore

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

sys.path.append(os.path.join(ROOT_DIR, '../..'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)


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

with pg.connect(connection_string) as connection:
    cursor = connection.cursor()
    try:
        cursor.execute('DROP TABLE {0};'.format(postgres['table_name']))
        logger.info(f"Table {postgres['table_name']} dropped")
    except Exception as e:
        logger.exception(f"Table {postgres['table_name']} didn't exist. Error: {str(e)}")
