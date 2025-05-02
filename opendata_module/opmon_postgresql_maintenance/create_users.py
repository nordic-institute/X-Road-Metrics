#!/usr/bin/env python3
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

"""
Script to create PostgreSQL users for X-Road Metrics tools.
"""

import argparse
import getpass
import logging
import secrets
import string
from typing import Dict

import psycopg2
import yaml
from psycopg2 import errors as psycopg2_errors
from psycopg2.extensions import (ISOLATION_LEVEL_AUTOCOMMIT,
                                 ISOLATION_LEVEL_DEFAULT, QuotedString)

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


full_users = {'anonymizer'}
read_only_users = {'opendata', 'networking'}


def main():
    args = _parse_args()
    postgres_conn = _connect_postgres(args)

    # it is not allowed to create database in transaction context
    postgres_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        _create_database(args, postgres_conn)
        logger.info('Database created successfully')
    except psycopg2_errors.DuplicateDatabase as e:
        logger.info(f'Nothing to do: {str(e)}')

    if args.remove_existing_users:
        users_to_remove = [f'{user}_{args.xroad}' for user in full_users | read_only_users]
        logger.info(f'Will try to remove DB users {users_to_remove}\n')
        _remove_users(args, postgres_conn)

    # create users and grant permissions in single transaction
    postgres_conn.set_isolation_level(ISOLATION_LEVEL_DEFAULT)
    try:
        passwords = _create_users(args, postgres_conn)
        _grant_privileges(args, postgres_conn)
        postgres_conn.commit()
        _print_users(passwords)
    except psycopg2_errors.DuplicateObject as e:
        logger.info(str(e))


def _remove_users(args: argparse.Namespace,
                  postgres_conn: psycopg2.extensions.connection) -> None:
    """
    Removes users associated with the specified XRoad instance from the database.

        :param args: Arguments passed to the function.
        :param postgres_conn: Postgres connection object.
    """

    database = f'opendata_{args.xroad}'
    cursor = postgres_conn.cursor()

    for user_prefix in full_users:
        user = f'{user_prefix}_{args.xroad}'
        revoke_sql = f'REVOKE CREATE, CONNECT ON DATABASE {database} FROM {user};'
        drop_user_sql = f'DROP USER {user};'
        try:
            cursor.execute(revoke_sql)
            cursor.execute(drop_user_sql)
            logger.info(f'{user} removed successfully')
        except psycopg2.errors.UndefinedObject as e:
            logger.info(f'Trying to remove full user {user}: {str(e)}')

    for user_prefix in read_only_users:
        user = f'{user_prefix}_{args.xroad}'
        revoke_sql = f'REVOKE CONNECT ON DATABASE {database} FROM {user};'
        drop_user_sql = f'DROP USER {user};'
        try:
            cursor.execute(revoke_sql)
            cursor.execute(drop_user_sql)
            logger.info(f'{user} removed successfully')
        except psycopg2.errors.UndefinedObject as e:
            logger.info(f'Trying to remove read only {user}: {str(e)}')


def _connect_postgres(args: argparse.Namespace) -> psycopg2.extensions.connection:
    """
    Establishes a connection to the PostgreSQL database.

    :param args: Arguments passed to the function.
    :return: A psycopg2 connection object.
    """
    connections_args = {
        'database': '',
        'user': args.user,
    }

    if args.host is not None:
        host, port = args.host.split(':')
        connections_args['host'] = host
        connections_args['port'] = int(port)

    if args.password is not None:
        connections_args['password'] = args.password
    elif args.prompt_password:
        connections_args['password'] = getpass.getpass()

    connection = psycopg2.connect(**connections_args)
    return connection


def _create_users(args: argparse.Namespace,
                  postgres_conn: psycopg2.extensions.connection) -> Dict[str, str]:
    """
    Create database users with passwords.

    :param args: Arguments passed to the function.
    :param postgres_conn: Postgres connection object.
    :return: A dictionary mapping created users to their passwords.
    """
    passwords = {}

    for user_prefix in full_users | read_only_users:
        user = f'{user_prefix}_{args.xroad}'
        password = user if args.dummy_passwords else _generate_password()
        passwords[user] = password

        quoted_password = QuotedString(password).getquoted().decode('utf-8')
        postgres_conn.cursor().execute(f'CREATE USER {user} WITH PASSWORD {quoted_password};')
    return passwords


def _create_database(args: argparse.Namespace,
                     postgres_conn: psycopg2.extensions.connection) -> None:
    """
    Creates a new database with the specified name using the template0 template.

    :param args: Arguments passed to the function.
    :param postgres_conn: Postgres connection object.
    """
    postgres_conn.cursor().execute(f"""
        CREATE DATABASE opendata_{args.xroad}
            WITH TEMPLATE template0
                ENCODING 'utf8'
                LC_COLLATE 'en_US.utf8'
                LC_CTYPE 'en_US.utf8';
        """)


def _grant_privileges(args: argparse.Namespace,
                      postgres_conn: psycopg2.extensions.connection) -> None:
    """
    Grants privileges on the database to the specified users.

    :param args: Arguments passed to the function.
    :param postgres_conn: Postgres connection object.
    """
    database = f'opendata_{args.xroad}'

    for user_prefix in full_users:
        user = f'{user_prefix}_{args.xroad}'
        postgres_conn.cursor().execute(f'GRANT CREATE, CONNECT ON DATABASE {database} TO {user} WITH GRANT OPTION;')

    for user_prefix in read_only_users:
        user = f'{user_prefix}_{args.xroad}'
        postgres_conn.cursor().execute(f'GRANT CONNECT ON DATABASE {database} TO {user} WITH GRANT OPTION;')


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('xroad', metavar='X-ROAD-INSTANCE', help='X-Road instance name.')

    parser.add_argument(
        '--host',
        metavar='HOST:PORT',
        default=None,
        help='PostgreSQL host:port. If omitted will try to connect locally using a Unix domain socket.'
    )

    parser.add_argument('--user', help='PostgreSQL admin username. Default is "postgres"', default='postgres')
    parser.add_argument(
        '--password',
        help='PostgreSQL admin password. By default no password is used.',
        default=None
    )
    parser.add_argument(
        '--prompt-password',
        action='store_true',
        help='Use interactive prompt to enter PostgreSQL admin password. Has no effect is --password argument is set'
    )
    parser.add_argument(
        '--dummy-passwords',
        action='store_true',
        help='Skip generation of secure passwords for users. Password will be same as username.'
    )
    parser.add_argument(
        '--remove-existing-users',
        action='store_true',
        help='Removes existing users from DB associated with the specified XRoad instance'
    )

    args = parser.parse_args()
    args.xroad = args.xroad.lower().replace('-', '_')

    return args


def _print_users(passwords: Dict[str, str]) -> None:
    width = max([len(k) for k in passwords.keys()]) + 1
    width = max(width, len('Username'))

    print('\nGenerated following users: \n')
    print(f'{"Username":<{width}}| {"Password":<{13}}| Escaped Password')
    print(f'{width * "-"}+{"-" * 14}+{"-" * 20}')
    [print(f'{user:<{width}}| {password} | {_escape_password(password)}') for user, password in passwords.items()]


def _get_password_character_set():
    """
    Generate a set of characters from which to compose a password.
    Some characters are avoided because they cause issues in a .yaml file, even after being escaped.
    """
    avoid_chars = "\\"
    allowed_character_set = "".join(
        c for c in (string.ascii_letters + string.digits + string.punctuation)
        if c not in avoid_chars
    )
    return allowed_character_set

def _generate_password():
    """
    Generate a random 12 character password.

    Password contains lower-case, upper-case, numbers and special characters.
    Based on best-practice recipe from https://docs.python.org/3/library/secrets.html.
    """
    alphabet = _get_password_character_set()
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3
                and any(c in string.punctuation for c in password)):
            return password


def _escape_password(password: str) -> str:
    return yaml.dump(password, default_style='"').strip()


if __name__ == '__main__':
    main()
