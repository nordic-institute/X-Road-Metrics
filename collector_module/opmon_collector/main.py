#!/usr/bin/env python3

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

import argparse
import sys

from opmon_collector.collector_multiprocessing import collector_main
from opmon_collector.update_servers import update_database_server_list, print_server_list
from opmon_collector.settings import OpmonSettingsManager


def main():
    args = parse_args()
    settings_manager = OpmonSettingsManager(args.profile)
    settings = settings_manager.settings

    actions = {
        'collect': (collector_main, [settings]),
        'update': (update_database_server_list, [settings]),
        'list': (print_server_list, [settings]),
        'settings': (settings_action_handler, [settings_manager, args])
    }

    action = actions[args.action]
    action[0](*action[1])


def parse_args():
    parser = argparse.ArgumentParser()

    actions = ['collect', 'update', 'list', 'settings']
    parser.add_argument("action",
                        metavar="ACTION",
                        choices=actions,
                        help=f"X-Road Metrics collector action to execute. Supported actions are {actions}")

    parser.add_argument('extra',
                        metavar="ARGS",
                        nargs=argparse.REMAINDER,
                        default='',
                        help='Arguments for action.')

    parser.add_argument("--profile",
                        metavar="PROFILE",
                        default=None,
                        help="""
                            Optional settings file profile.
                            For example with '--profile PROD' settings_PROD.yaml will be used as settings file.
                            If no profile is defined, settings.yaml will be used by default.
                            Settings file is searched from current working directory and /etc/xroad-metrics/collector/
                        """.strip()
                        )
    args = parser.parse_args()

    return args


def parse_setting_action_args(args):
    parser = argparse.ArgumentParser(prog=f'{sys.argv[0]} settings')
    parser.add_argument("action", metavar="ACTION", choices=['get'], help="Settings action to execute. Currently only option is 'get'.")
    parser.add_argument("keystring", metavar="SETTING", help="Name of the setting, e.g. 'mongodb.user'")
    return parser.parse_args(args.extra)


def settings_action_handler(settings_manager, args):
    settings_args = parse_setting_action_args(args)
    setting = settings_manager.get(settings_args.keystring)
    print(setting)
