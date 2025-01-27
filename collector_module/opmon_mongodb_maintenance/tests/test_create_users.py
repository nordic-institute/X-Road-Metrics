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
Unit tests for create_users.py
"""

from argparse import Namespace
import yaml
import opmon_mongodb_maintenance.create_users as create_users

opmon_user_names = ['analyzer', 'analyzer_interface', 'anonymizer', 'collector', 'corrector', 'reports']
admin_user_names = ['root', 'backup', 'superuser']


def test_admin_user_generation(mocker):
    args = Namespace(generate_admins=True, dummy_passwords=False)
    client = mocker.Mock()

    passwords = {}
    create_users._create_admin_users(args, client, passwords)

    client.admin.command.assert_called()
    assert client.admin.command.call_count == 3
    assert len(passwords) == 3
    assert len(set(passwords.values())) == 3  # passwords are unique
    for pwd in passwords.values():
        assert len(pwd) >= 12


def test_skipping_admin_user_generation(mocker):
    args = Namespace(generate_admins=False, dummy_passwords=False)
    client = mocker.Mock()

    passwords = {}
    create_users._create_admin_users(args, client, passwords)

    client.admin.command.assert_not_called()
    assert len(passwords) == 0


def test_admin_user_generation_without_passwords(mocker):
    args = Namespace(generate_admins=True, dummy_passwords=True)
    client = mocker.Mock()

    passwords = {}
    create_users._create_admin_users(args, client, passwords)

    client.admin.command.assert_called()
    assert client.admin.command.call_count == 3
    assert len(passwords) == 3
    for user, pwd in passwords.items():
        assert user == pwd


def test_opmon_user_generation(mocker):
    args = Namespace(xroad='XRD1', dummy_passwords=False, user_to_generate=None)
    client = mocker.Mock()

    passwords = {}
    create_users._create_opmon_users(args, client, passwords)

    client.auth_db.command.assert_called()
    assert client.auth_db.command.call_count == 6
    assert len(passwords) == 6
    assert len(set(passwords.values())) == 6  # passwords are unique

    for pwd in passwords.values():
        assert len(pwd) >= 12

    for user in opmon_user_names:
        to_find = f'{user}_{args.xroad}'
        assert to_find in passwords.keys()


def test_specific_metrics_user_generation(mocker):
    args = Namespace(xroad='XRD1', dummy_passwords=False, user_to_generate='opendata_collector')
    client = mocker.Mock()

    passwords = {}
    create_users._create_opmon_users(args, client, passwords)
    client.auth_db.command.assert_called()
    assert client.auth_db.command.call_count == 1
    assert len(passwords) == 1
    assert len(set(passwords.values())) == 1  # passwords are unique

    for pwd in passwords.values():
        assert len(pwd) >= 12

    for user in opmon_user_names:
        to_find = f'opendata_collector_{args.xroad}'
        assert to_find in passwords.keys()


def test_opmon_user_generation_without_passwords(mocker):
    args = Namespace(xroad='XRD2', dummy_passwords=True, user_to_generate=None)
    client = mocker.Mock()

    passwords = {}
    create_users._create_opmon_users(args, client, passwords)

    client.auth_db.command.assert_called()
    assert client.auth_db.command.call_count == 6
    assert len(set(passwords.values())) == 6  # passwords are unique

    for user, pwd in passwords.items():
        assert user == pwd

    assert len(passwords.keys()) == 6
    for user in opmon_user_names:
        to_find = f'{user}_{args.xroad}'
        assert to_find in passwords.keys()


def test_password_escaping():
    password = """:/foo'"\\_*{}[]''"""
    escaped_password = create_users._escape_password(password)
    assert escaped_password == '":/foo\'\\"\\\\_*{}[]\'\'"'
    assert yaml.safe_load(escaped_password) == password


def test_print_users():
    create_users._print_users({
        'foo': '123456789012',
        'bar': """:/o'"\\_*{}''"""
    })
