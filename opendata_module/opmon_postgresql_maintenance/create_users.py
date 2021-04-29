#!/usr/bin/env python3

"""
Script to create PostgreSQL users for X-Road OpMon tools.
"""

import argparse
import getpass
import psycopg2
import yaml
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extensions import QuotedString
import string
import secrets

full_users = {"anonymizer"}
read_only_users = {"opendata", "networking"}


def main():
    args = _parse_args()
    postgres = _connect_postgres(args)
    passwords = _create_users(args, postgres)
    _create_database(args, postgres)
    _grant_privileges(args, postgres)
    _print_users(passwords)


def _connect_postgres(args):
    connections_args = {
        'database': "",
        'user': args.user,
    }

    if args.host is not None:
        host, port = args.host.split(":")
        connections_args['host'] = host
        connections_args['port'] = int(port)

    if args.password is not None:
        connections_args['password'] = args.password
    elif args.prompt_password:
        connections_args['password'] = getpass.getpass()

    connection = psycopg2.connect(**connections_args)
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return connection.cursor()


def _create_users(args, postgres):
    passwords = {}
    for user_prefix in full_users | read_only_users:
        user = f"{user_prefix}_{args.xroad}"
        password = user if args.dummy_passwords else _generate_password()
        passwords[user] = password

        quoted_password = QuotedString(password).getquoted().decode('utf-8')
        postgres.execute(f"CREATE USER {user} WITH PASSWORD {quoted_password};")

    return passwords


def _create_database(args, postgres):
    postgres.execute(f"""
        CREATE DATABASE opendata_{args.xroad} 
            WITH TEMPLATE template0 
                ENCODING 'utf8' 
                LC_COLLATE 'en_US.utf8' 
                LC_CTYPE 'en_US.utf8';
    """)


def _grant_privileges(args, postgres):
    database = f"opendata_{args.xroad}"

    for user_prefix in full_users:
        user = f"{user_prefix}_{args.xroad}"
        postgres.execute(f"GRANT CREATE, CONNECT ON DATABASE {database} TO {user} WITH GRANT OPTION;")

    for user_prefix in read_only_users:
        user = f"{user_prefix}_{args.xroad}"
        postgres.execute(f"GRANT CONNECT ON DATABASE {database} TO {user} WITH GRANT OPTION;")


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("xroad", metavar="X-ROAD-INSTANCE", help="X-Road instance name.")

    parser.add_argument(
        "--host",
        metavar="HOST:PORT",
        default=None,
        help="PostgreSQL host:port. If omitted will try to connect locally using a Unix domain socket."
    )

    parser.add_argument("--user", help='PostgreSQL admin username. Default is "postgres"', default='postgres')
    parser.add_argument(
        "--password",
        help='PostgreSQL admin password. By default no password is used.',
        default=None
    )
    parser.add_argument(
        "--prompt-password",
        action="store_true",
        help="Use interactive prompt to enter PostgreSQL admin password. Has no effect is --password argument is set"
    )
    parser.add_argument(
        "--dummy-passwords",
        action="store_true",
        help="Skip generation of secure passwords for users. Password will be same as username."
    )

    args = parser.parse_args()
    args.xroad = args.xroad.lower().replace('-', '_')

    return args


def _print_users(passwords):
    width = max([len(k) for k in passwords.keys()]) + 1
    width = max(width, len("Username"))

    print("\nGenerated following users: \n")
    print(f'{"Username":<{width}}| {"Password":<{13}}| Escaped Password')
    print(f'{width * "-"}+{"-" * 14}+{"-" * 20}')
    [print(f'{user:<{width}}| {password} | {_escape_password(password)}') for user, password in passwords.items()]


def _generate_password():
    """
    Generate a random 12 character password.
    
    Password contains lower-case, upper-case, numbers and special characters.
    Based on best-practice recipe from https://docs.python.org/3/library/secrets.html.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3
                and any(c in string.punctuation for c in password)):
            return password


def _escape_password(password):
    return yaml.dump(password, default_style='"').strip()


if __name__ == '__main__':
    main()
