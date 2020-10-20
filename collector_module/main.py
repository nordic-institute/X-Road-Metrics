#!/usr/bin/env python3

import argparse
import collector_worker
import os
import importlib.util
import re

from settings import OpmonSettings
import update_servers
# import list_servers


def main():
    args = parse_args()
        
    actions = {
        'collect': collector_worker.main,
        'update': update_servers.main,
        # 'list': list_servers.main,
        'settings': settings_action_handler
    }

    settings = OpmonSettings(args.xroad).settings
    actions[args.action](settings, args)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", metavar="ACTION", choices=['collect', 'list', 'update', 'settings'], help="OpMon collector action to execute.")
    parser.add_argument('extra', metavar="ARGS", nargs=argparse.REMAINDER, default='', help='Arguments for action.')
    parser.add_argument("--xroad", metavar="X-ROAD-INSTANCE", default=None, help="""
            Optional X-Road instance name.
            If set to VALUE, X-Road settings from settings_VALUE.py will be used.
            If not set, default settings file will be used.
        """.strip()
    )
    args = parser.parse_args()

    return args


def parse_setting_action_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", metavar="ACTION", choices=['get'], help="Settings action to execute. Currently only option is 'get'.")
    parser.add_argument("setting", metavar="SETTING", help="Name of the setting, e.g. 'mongodb.user'")
    return parser.parse_args(args.extra)


def settings_action_handler(settings, args):
    settings_args = parse_setting_action_args(args)

    keys = list(filter(None, re.split(r'\.|\[|\]', settings_args.setting)))
    value = settings
    for k in keys:
        value = value[k if not k.isdigit() else int(k)]

    print(value)


if __name__ == '__main__':
    main()
