import psycopg2 as pg
import os
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

sys.path.append(os.path.join(ROOT_DIR, '../..'))

from settings import postgres


def get_connection_string(
        host_address=None, port=None, database_name=None, user=None, password=None, **irrelevant_settings):
    string_parts = ["host={host} dbname={dbname}".format(
        **{'host': host_address, 'dbname': database_name})]

    if port:
        string_parts.append("port=" + str(port))

    if user:
        string_parts.append("user=" + user)

    if password:
        string_parts.append("password=" + password)

    return ' '.join(string_parts)

connection_string = get_connection_string(**postgres)

with pg.connect(connection_string) as connection:
    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE {0};".format(postgres['table_name']))
        print("Table {0} dropped".format(postgres['table_name']))
    except:
        print("Table {0} didn't exist".format(postgres['table_name']))
