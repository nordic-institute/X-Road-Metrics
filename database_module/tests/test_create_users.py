#!/usr/bin/env python3

"""
Unit tests for create_users.py
"""
import create_users
import pytest
from argparse import Namespace

opmon_user_names = ['analyzer', 'analyzer_interface', 'anonymizer', 'collector', 'corrector', 'reports']
admin_user_names = ['root', 'backup', 'superuser']


def test_admin_user_generation(mocker):
    args = Namespace(generate_admins=True, no_passwords=False)
    client = mocker.Mock()

    passwords = {}
    create_users._create_admin_users(args, client, passwords)

    client.admin.command.assert_called()
    assert client.admin.command.call_count == 3
    assert len(passwords) == 3
    assert len(set(passwords.values())) == 3  # passwords are unique
    for pwd in passwords.values():
        assert len(pwd) >= 12

"""
def test_skipping_admin_user_generation(self):
    args=Namespace(generate_admins = False, no_passwords = False)
    client=Mock()

    passwords={}
    create_users._create_admin_users(args, client, passwords)

    client.admin.command.assert_not_called()
    self.assertEqual(len(passwords), 0)


def test_admin_user_generation_without_passwords(self):
    args=Namespace(generate_admins = True, no_passwords = True)
    client=Mock()

    passwords={}
    create_users._create_admin_users(args, client, passwords)

    client.admin.command.assert_called()
    self.assertEqual(client.admin.command.call_count, 3)
    self.assertEqual(len(passwords), 3)
    for user, pwd in passwords.items():
        self.assertEqual(user, pwd)


def test_opmon_user_generation(self):
    args=Namespace(xroad = 'XRD1', no_passwords = False)
    client=Mock()

    passwords={}
    create_users._create_opmon_users(args, client, passwords)

    client.auth_db.command.assert_called()
    self.assertEqual(client.auth_db.command.call_count, 6)
    self.assertEqual(len(passwords), 6)
    self.assertEqual(len(set(passwords.values())), 6)  # passwords are unique

    for pwd in passwords.values():
        self.assertGreaterEqual(len(pwd), 12)

    for user in self.opmon_user_names:
        to_find=f'{user}_{args.xroad}'
        self.assertTrue(to_find in passwords.keys())


def test_opmon_user_generation_without_passwords(self):
    args=Namespace(xroad = 'XRD2', no_passwords = True)
    client=Mock()

    passwords={}
    create_users._create_opmon_users(args, client, passwords)

    client.auth_db.command.assert_called()
    self.assertEqual(client.auth_db.command.call_count, 6)
    self.assertEqual(len(set(passwords.values())), 6)  # passwords are unique

    for user, pwd in passwords.items():
        self.assertEqual(user, pwd)

    self.assertEqual(len(passwords.keys()), 6)
    for user in self.opmon_user_names:
        to_find=f'{user}_{args.xroad}'
        self.assertTrue(to_find in passwords.keys())
"""
