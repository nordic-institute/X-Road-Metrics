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
        self.assertTrue("root" in passwords.keys())
        self.assertTrue("backup" in passwords.keys())
        self.assertTrue("superuser" in passwords.keys())


if __name__ == '__main__':
    unittest.main()
