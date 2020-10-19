#!/usr/bin/env python3

import argparse
import collector_worker
import os
import importlib.util

from settings import OpmonSettings
# import update_servers
# import list_servers


def main():
    args = parse_args()
    commands = {
        'collect': collector_worker.main
        # 'update': update_servers.main,
        # 'list': list_servers.main
    }

    settings = OpmonSettings(args.xroad).settings
    commands[args.action](settings)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", metavar="ACTION", choices=['collect', 'list', 'update'], help="OpMon collector action to execute.")
    parser.add_argument("--xroad", metavar="X-ROAD-INSTANCE", default=None, help="""
            Optional X-Road instance name.
            If set to VALUE, X-Road settings from settings_VALUE.py will be used.
            If not set, default settings file will be used.
        """.strip()
    )
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
