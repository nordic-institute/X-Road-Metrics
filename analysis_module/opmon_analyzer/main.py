#!/usr/bin/env python3

import argparse

from .settings_parser import OpmonSettingsManager
from .train_or_update_historic_averages_models import update_model
from .find_anomalies import find_anomalies


def main():
    args = parse_args()
    settings_manager = OpmonSettingsManager(args.profile)
    settings = settings_manager.settings

    actions = {
        'update': (update_model, [settings]),
        'find': (find_anomalies, [settings])
    }

    action = actions[args.action]

    print('action')

    action[0](*action[1])


def parse_args():
    parser = argparse.ArgumentParser()

    actions = ['update', 'find']
    parser.add_argument("action",
                        metavar="ACTION",
                        choices=actions,
                        help=f"OpMon collector action to execute. Supported actions are {actions}")

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
                            Settings file is searched from current working directory and /etc/opmon/analyzer/
                        """.strip()
                        )
    args = parser.parse_args()

    return args
