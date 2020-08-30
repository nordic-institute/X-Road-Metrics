import psycopg2 as pg
import os
import sys
import csv

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

sys.path.append(os.path.join(ROOT_DIR, '../../interface/'))

from settings import POSTGRES_CONFIG


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


def get_schema_command():
    with open(os.path.join(ROOT_DIR, 'schema.sql')) as schema_file:
        return schema_file.read().strip()


def get_index_creation_commands():
    with open(os.path.join(ROOT_DIR, 'indices.sql')) as indices_file:
        return [index_line.strip() for index_line in indices_file]


def get_data():
    with open(os.path.join(ROOT_DIR, 'sample.tsv')) as data_file:
        reader = csv.reader(data_file, delimiter='\t')
        return [[value if value != '\\N' else None for value in row] for row in reader]

connection_string = get_connection_string(**POSTGRES_CONFIG)

schema_command = get_schema_command()
index_creation_commands = get_index_creation_commands()
data = get_data()

with pg.connect(connection_string) as connection:
    cursor = connection.cursor()
    cursor.execute(schema_command)
    for index_creation_command in index_creation_commands:
        cursor.execute(index_creation_command)
    insertion_str = ','.join(
        cursor.mogrify("({0})".format(','.join(['%s'] * len(row))), row).decode('utf8') for row in data)
    cursor.execute("INSERT INTO {0} VALUES {1};".format(POSTGRES_CONFIG['table_name'], insertion_str))
