#!/usr/bin/env python3

"""
Script to create MongoDb users for X-Road OpMon tools.
"""

from pymongo import MongoClient
import sys
import argparse
import string
import secrets

user_roles = {
    'analyzer': {'query_db': 'read', 'analyzer_database': 'readWrite'},
    'analyzer_interface': {'query_db': 'read', 'analyzer_database': 'readWrite'},
    'anonymizer': {'query_db': 'read', 'anonymizer_state': 'readWrite'},
    'collector': {'query_db': 'readWrite', 'collcetor_state': 'readWrite'},
    'corrector': {'query_db': 'readWrite'},
    'reports': {'query_db': 'read', 'reports_state': 'readWrite'}
}

admin_roles = {
    'root': ['root'],
    'backup': ['backup'],
    'superuser': ['root']
}


def main():
    passwords = {}
    args = _parse_args()
    client = MongoClient(args.mongodb_host)

    _create_admin_users(args, client, passwords)
    _create_opmon_users(args, client, passwords)
    _print_users(passwords)


def _create_admin_users(args, client, passwords):
    if not args.generate_admins:
        return

    for user_name, roles in admin_roles.items():
        passwords[user_name] = user_name if args.no_passwords else _generate_password()
        client.admin.command('createUser', user_name, pwd=passwords[user_name], roles=roles)


def _create_opmon_users(args, client, passwords):
    for user, roles in user_roles.items():
        user_name = '{}_{}'.format(user, args.xroad)
        role_list = _roles_to_list(roles)
        passwords[user_name] = user_name if args.no_passwords else _generate_password()

        client.auth_db.command('createUser', user_name, pwd=passwords[user_name], roles=role_list)


def _roles_to_list(roles):
    return [{'db': db, 'role': role} for db, role in roles.items()]


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("xroad", help="X-Road instance name")
    parser.add_argument("--mongodb-host", "-m", default="localhost:27017", help="MongoDb host:port. Default is localhost:27017")
    parser.add_argument("--no-passwords", "-np", action="store_true", help="Skip generation of secure passwords for users. Password will be equal to username.")
    parser.add_argument("--generate-admins", "-a", action="store_true", help="Also generate admin users.")
    args = parser.parse_args()

    return args


def _print_users(passwords):
    width = max([len(k) for k in passwords.keys()]) + 1

    print("\nGenerated following users: \n")
    print(f'{"Username":<{width}}| Password')
    print(f'{width * "-"}+{"-"*20}')
    [print(f'{user:<{width}}| {password}') for user, password in passwords.items()]


def _generate_password():
    special_chars = """!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"""
    alphabet = string.ascii_letters + string.digits + special_chars
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3
                and any(c in special_chars for c in password)):
            return password


if __name__ == '__main__':
    main()
