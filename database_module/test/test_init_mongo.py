#!/usr/bin/env python3

"""
Unit tests for init_mongo.py
"""

import init_mongo
import unittest
from unittest.mock import Mock
from argparse import Namespace


class TestInitMongo(unittest.TestCase):
    def test_admin_user_generation(self):
        args = Namespace(generate_admins=True, no_passwords=False)
        client = Mock()

        passwords = {}
        init_mongo._create_admin_users(args, client, passwords)

        client.admin.command.assert_called()
        self.assertEqual(client.admin.command.call_count, 3)
        self.assertEqual(len(passwords), 3)
        self.assertEqual(len(set(passwords.values())), 3)  # passwords are unique
        for pwd in passwords.values():
            self.assertGreaterEqual(len(pwd), 12)

    def test_skipping_admin_user_generation(self):
        args = Namespace(generate_admins=False, no_passwords=False)
        client = Mock()

        passwords = {}
        init_mongo._create_admin_users(args, client, passwords)

        client.admin.command.assert_not_called()
        self.assertEqual(len(passwords), 0)

    def test_admin_user_generation_without_passwords(self):
        args = Namespace(generate_admins=True, no_passwords=True)
        client = Mock()

        passwords = {}
        init_mongo._create_admin_users(args, client, passwords)

        client.admin.command.assert_called()
        self.assertEqual(client.admin.command.call_count, 3)
        self.assertEqual(len(passwords), 3)
        for user, pwd in passwords.items():
            self.assertGreaterEqual(user, pwd)


if __name__ == '__main__':
    unittest.main()
