#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

from unittest.mock import call

from psycopg2.extensions import QuotedString
import yaml
import opmon_postgresql_maintenance.create_users as create_users
from argparse import Namespace


def test_connect_postgres_defaults(mocker):
    mocker.patch('opmon_postgresql_maintenance.create_users.psycopg2.connect', return_value=mocker.Mock())
    args = Namespace(
        user='postgres',
        host=None,
        password=None,
        prompt_password=False
    )
    create_users._connect_postgres(args)

    create_users.psycopg2.connect.assert_called_once_with(database='', user='postgres')


def test_connect_postgres_with_host(mocker):
    mocker.patch('opmon_postgresql_maintenance.create_users.psycopg2.connect', return_value=mocker.Mock())
    args = Namespace(
        user='postgres',
        host='myhost:1234',
        password=None,
        prompt_password=False
    )
    create_users._connect_postgres(args)
    create_users.psycopg2.connect.assert_called_once_with(database='', host='myhost', port=1234, user='postgres')


def test_connect_postgres_with_user_and_password(mocker):
    mocker.patch('opmon_postgresql_maintenance.create_users.psycopg2.connect', return_value=mocker.Mock())
    mocker.patch('opmon_postgresql_maintenance.create_users.getpass.getpass', return_value='testpass')
    args = Namespace(
        host='myhost:1234',
        user='me',
        password='mypass',
        prompt_password=True
    )
    create_users._connect_postgres(args)
    create_users.psycopg2.connect.assert_called_once_with(
        database='',
        host='myhost',
        port=1234,
        user='me',
        password='mypass',
    )


def test_connect_postgres_with_password_prompt(mocker):
    mocker.patch('opmon_postgresql_maintenance.create_users.psycopg2.connect', return_value=mocker.Mock())
    mocker.patch('opmon_postgresql_maintenance.create_users.getpass.getpass', return_value='testpass')
    args = Namespace(
        host='myhost:1234',
        user='me',
        password=None,
        prompt_password=True
    )
    create_users._connect_postgres(args)
    create_users.psycopg2.connect.assert_called_once_with(
        database='',
        user='me',
        host='myhost',
        port=1234,
        password='testpass'
    )


def test_create_users(mocker):
    postgres = mocker.Mock()
    postgres.execute = mocker.Mock(return_value='passwords')

    args = Namespace(xroad="foo", dummy_passwords=False)
    passwords = create_users._create_users(args, postgres)

    assert postgres.execute.call_count == len(create_users.full_users) + len(create_users.read_only_users)

    for user, pwd in passwords.items():
        assert user.endswith('_foo')
        assert len(pwd) == 12
        quoted_password = QuotedString(pwd).getquoted().decode('utf-8')
        expected_call = call(f"CREATE USER {user} WITH PASSWORD {quoted_password};")
        assert expected_call in postgres.execute.call_args_list


def test_create_users_with_dummy_passwords(mocker):
    postgres = mocker.Mock()
    postgres.execute = mocker.Mock(return_value='passwords')

    args = Namespace(xroad="foo", dummy_passwords=True)
    passwords = create_users._create_users(args, postgres)

    assert postgres.execute.call_count == len(create_users.full_users) + len(create_users.read_only_users)

    for user, pwd in passwords.items():
        assert user.endswith('_foo')
        assert pwd == user
        quoted_password = QuotedString(pwd).getquoted().decode('utf-8')
        expected_call = call(f"CREATE USER {user} WITH PASSWORD {quoted_password};")
        assert expected_call in postgres.execute.call_args_list


def test_create_database(mocker):
    postgres = mocker.Mock()
    postgres.execute = mocker.Mock(return_value='passwords')

    args = Namespace(xroad="foo")
    create_users._create_database(args, postgres)

    postgres.execute.assert_called_once()
    pretty_args = ' '.join(postgres.execute.call_args[0][0].replace('\n', ' ').split())
    assert pretty_args == "CREATE DATABASE opendata_foo WITH TEMPLATE template0 ENCODING 'utf8' " \
           + "LC_COLLATE 'en_US.utf8' LC_CTYPE 'en_US.utf8';"


def test_grant_priviledges(mocker):
    postgres = mocker.Mock()
    postgres.execute = mocker.Mock(return_value='passwords')

    args = Namespace(xroad="foo", dummy_passwords=True)
    create_users._grant_privileges(args, postgres)

    assert postgres.execute.call_count == len(create_users.full_users) + len(create_users.read_only_users)
    for call in postgres.execute.call_args_list:
        assert call.args[0].startswith('GRANT')


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
