#!/usr/bin/env python3

import argparse
import collector_worker
# import update_servers
# import list_servers
import os
import importlib.util


def main():
    args = parse_args()
    commands = {
        'collect': collector_worker.main
        # 'update': update_servers.main,
        # 'list': list_servers.main
    }

    settings = import_settings(args.xroad)

    print(dir(settings))

    commands[args.action](settings)


def import_settings(xroad_instance):
    filename = 'settings.py' if xroad_instance is None else f'settings_{xroad_instance}.py'
    path = '.' if os.path.isfile(filename) else '/etc/opmon/collector_module/'

    spec = importlib.util.spec_from_file_location("settings", path + filename)
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    return settings


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
