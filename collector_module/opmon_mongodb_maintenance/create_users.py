#!/usr/bin/env python3

"""
Script to create MongoDb users for X-Road Metrics tools.
"""

import string
import secrets

import yaml

user_roles = {
    'analyzer': {'query_db': 'read', 'analyzer_database': 'readWrite'},
    'analyzer_interface': {'query_db': 'read', 'analyzer_database': 'readWrite'},
    'anonymizer': {'query_db': 'read', 'anonymizer_state': 'readWrite'},
    'collector': {'query_db': 'readWrite', 'collector_state': 'readWrite'},
    'corrector': {'query_db': 'readWrite'},
    'reports': {'query_db': 'read', 'reports_state': 'readWrite'}
}

admin_roles = {
    'root': ['root'],
    'backup': ['backup'],
    'superuser': ['root']
}


def create_users(args, client):
    passwords = {}

    _create_admin_users(args, client, passwords)
    _create_opmon_users(args, client, passwords)
    _print_users(passwords)


def _create_admin_users(args, client, passwords):
    if not args.generate_admins:
        return

    for user_name, roles in admin_roles.items():
        try:
            password = user_name if args.dummy_passwords else _generate_password()
            client.admin.command('createUser', user_name, pwd=password, roles=roles)
            passwords[user_name] = password
        except Exception as e:
            print(f"Failed to create user {user_name}: {e}")


def _create_opmon_users(args, client, passwords):
    for user, roles in user_roles.items():
        user_name = f'{user}_{args.xroad}'
        role_list = [{'db': f'{db}_{args.xroad}', 'role': role} for db, role in roles.items()]
        password = user_name if args.dummy_passwords else _generate_password()

        try:
            client.auth_db.command('createUser', user_name, pwd=password, roles=role_list)
            passwords[user_name] = password
        except Exception as e:
            print(f"Failed to create user {user_name}: {e}")


def _print_users(passwords: dict):
    if len(passwords) == 0:
        print("No users created.")
        return

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
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3
                and any(c in string.punctuation for c in password)):
            return password


def _escape_password(password):
    return yaml.dump(password, default_style='"').strip()
