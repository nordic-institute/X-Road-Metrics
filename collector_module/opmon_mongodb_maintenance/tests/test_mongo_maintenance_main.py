from argparse import Namespace
from opmon_mongodb_maintenance import main


def test_mongo_client_creation_no_auth(mocker):
    args = Namespace(host='testhost:1234', user=None)

    mocker.patch('opmon_mongodb_maintenance.main.MongoClient')
    main._connect_mongo(args)
    main.MongoClient.assert_called_once_with(args.host)


def test_mongo_client_creation_username_only(mocker):
    args = Namespace(host='testhost:1234', user='testuser', password=None, auth='admin')

    mocker.patch('opmon_mongodb_maintenance.main.MongoClient')
    mocker.patch('opmon_mongodb_maintenance.main.getpass.getpass', return_value='testpass')
    main._connect_mongo(args)

    main.MongoClient.assert_called_once_with(args.host, username=args.user, password='testpass', authSource=args.auth)
    main.getpass.getpass.assert_called_once()


def test_mongo_client_creation_full_auth(mocker):
    args = Namespace(host='testhost:1234', user='testuser', password='pass', auth='admin')

    mocker.patch('opmon_mongodb_maintenance.main.MongoClient')
    mocker.patch('opmon_mongodb_maintenance.main.getpass.getpass', return_value='wrongpass')
    main._connect_mongo(args)

    main.MongoClient.assert_called_once_with(args.host, username=args.user, password=args.password,
                                             authSource=args.auth)
    main.getpass.getpass.assert_not_called()
