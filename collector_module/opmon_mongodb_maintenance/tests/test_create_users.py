#!/usr/bin/env python3

"""
Unit tests for create_users.py
"""
import opmon_mongodb_maintenance.create_users as create_users
import pytest
from pytest_mock import mocker
from argparse import Namespace

opmon_user_names = ['analyzer', 'analyzer_interface', 'anonymizer', 'collector', 'corrector', 'reports']
admin_user_names = ['root', 'backup', 'superuser']


def test_mongo_client_creation_no_auth(mocker):
    args = Namespace(host='testhost:1234', user=None)

    mocker.patch('opmon_mongodb_maintenance.create_users.MongoClient')
    create_users._connect_mongo(args)
    create_users.MongoClient.assert_called_once_with(args.host)


def test_mongo_client_creation_username_only(mocker):
    args = Namespace(host='testhost:1234', user='testuser', password=None, auth='admin')

    mocker.patch('opmon_mongodb_maintenance.create_users.MongoClient')
    mocker.patch('opmon_mongodb_maintenance.create_users.getpass.getpass', return_value='testpass')
    create_users._connect_mongo(args)

    create_users.MongoClient.assert_called_once_with(args.host, username=args.user, password='testpass', authSource=args.auth)
    create_users.getpass.getpass.assert_called_once()


def test_mongo_client_creation_full_auth(mocker):
    args = Namespace(host='testhost:1234', user='testuser', password='pass', auth='admin')

    mocker.patch('opmon_mongodb_maintenance.create_users.MongoClient')
    mocker.patch('opmon_mongodb_maintenance.create_users.getpass.getpass', return_value='wrongpass')
    create_users._connect_mongo(args)

    create_users.MongoClient.assert_called_once_with(args.host, username=args.user, password=args.password, authSource=args.auth)
    create_users.getpass.getpass.assert_not_called()


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
    args = Namespace(xroad='XRD1', dummy_passwords=False)
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


def test_opmon_user_generation_without_passwords(mocker):
    args = Namespace(xroad='XRD2', dummy_passwords=True)
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
