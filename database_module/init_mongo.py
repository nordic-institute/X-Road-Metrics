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


def main():
    args = _parse_args()
    client = MongoClient(args.mongodb_host)
    # client.admin.authenticate('siteRootAdmin', 'Test123')

    passwords = {}

    for user, roles in user_roles.items():
        db_name = 'auth_db'
        user_name = '{}_{}'.format(user, args.xroad)
        role_list = _roles_to_list(roles)
        password = _generate_password()
        
        print(user, role_list)

        client[db_name].command('createUser', user_name, pwd=password, roles=role_list)

        passwords[user_name] = password
    
    _print_users(passwords)


def _roles_to_list(roles):
    role_list = []
    for db, role in roles.items():
        role_list.append({'db': db, 'role': role})
    return role_list


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("xroad", help="X-Road instance name")
    parser.add_argument("--mongodb-host", "-m", default="localhost:27017", help="MongoDb host:port. Default is localhost:27017")
    parser.add_argument("--no-passwords", "-np", action="store_true", help="Skip generation of secure passwords for users.")
    args = parser.parse_args()

    return args


def _print_users(passwords):
    width = max([len(k) for k in passwords.keys()]) + 1
    print("\nGenerated following users: \n")
    print("{:<{}}| {:<20}".format('User', width, 'Password'))
    print("{:<{}}+{:<20}".format('-' * width, width, '-' * 20))
    [print("{:<{}}| {:<20}".format(key, width, value)) for key, value in passwords.items()]


def _generate_password():
    special_chars = """@"'!#%&/()[]-_.,^*\\"""
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
