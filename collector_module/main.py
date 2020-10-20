#!/usr/bin/env python3

import argparse
import collector_worker
import os
import importlib.util
import re
import sys

from settings import OpmonSettingsManager
import update_servers


def main():
    args = parse_args()
    settings_manager = OpmonSettingsManager(args.xroad)
    settings = settings_manager.settings

    actions = {
        'collect': (collector_worker.main, [settings]),
        'update': (update_servers.update_database_server_list, [settings]),
        'list': (update_servers.print_server_list, [settings]),
        'settings': (settings_action_handler, [settings_manager, args])
    }

    action = actions[args.action]
    action[0](*action[1])


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("action",
                        metavar="ACTION",
                        choices=['collect', 'update', 'list', 'settings'],
                        help="OpMon collector action to execute.")

    parser.add_argument('extra',
                        metavar="ARGS",
                        nargs=argparse.REMAINDER,
                        default='',
                        help='Arguments for action.')

    parser.add_argument("--xroad",
                        metavar="X-ROAD-INSTANCE",
                        default=None,
                        help="""
                            Optional X-Road instance name.
                            If set to VALUE, X-Road settings from settings_VALUE.py will be used.
                            If not set, default settings file will be used.
                        """.strip()
                        )
    args = parser.parse_args()

    return args


def parse_setting_action_args(args):
    parser = argparse.ArgumentParser(prog=f'{sys.argv[0]} settings')
    parser.add_argument("action", metavar="ACTION", choices=['get'], help="Settings action to execute. Currently only option is 'get'.")
    parser.add_argument("setting", metavar="SETTING", help="Name of the setting, e.g. 'mongodb.user'")
    return parser.parse_args(args.extra)


def settings_action_handler(settings_manager, args):
    settings_args = parse_setting_action_args(args)
    settings_manager.print_setting(settings_args.setting)


if __name__ == '__main__':
    main()
