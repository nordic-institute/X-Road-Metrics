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

from opmon_reports import time_date_tools
from .settings_parser import OpmonSettingsManager
from .time_date_tools import date_to_timestamp_milliseconds, string_to_date


class OpmonReportsArguments:
    def __init__(self):
        args = self._parse_args()

        self.settings = OpmonSettingsManager(args.profile).settings
        self.action = args.action

        self.xroad_instance = self.settings['xroad']['instance']
        self.subsystem = self._parse_subsystem(args)

        self.start_date = args.start_date
        self.end_date = args.end_date
        self.language = args.language

        if self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date.")

    @property
    def start_time_milliseconds(self):
        return date_to_timestamp_milliseconds(string_to_date(self.start_date))

    @property
    def end_time_milliseconds(self):
        return date_to_timestamp_milliseconds(string_to_date(self.end_date), start_date=False)

    def _parse_subsystem(self, args):
        if args.subsystem is None:
            return None

        codes = args.subsystem.split(':')
        if len(codes) != 3:
            raise ValueError(
                "X-Road subsystem must be in format CLASS:MEMBER:SUBSYSTEM. For example ORG:1234:MYSUB")
        keys = ['member_class', 'member_code', 'subsystem_code']
        subsystem_dict = dict(zip(keys, codes))
        subsystem_dict['email'] = [{'email': args.email, 'name': ''}]
        subsystem_dict['x_road_instance'] = self.xroad_instance
        return subsystem_dict

    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser()

        start_date_default = time_date_tools.get_previous_month_first_day().isoformat()
        end_date_default = time_date_tools.get_previous_month_last_day().isoformat()

        actions = ['report', 'notify']
        parser.add_argument(
            "action",
            metavar="ACTION",
            choices=actions,
            help=f"X-Road Metrics Reports action to execute. Supported actions are {actions}"
        )

        parser.add_argument(
            "--profile",
            metavar="PROFILE",
            default=None,
            help="""
                Optional settings file profile.
                For example with '--profile PROD' settings_PROD.yaml will be used as settings file.
                If no profile is defined, settings.yaml will be used by default.
                Settings file is searched from current working directory and /etc/xroad-metrics/reports/
            """
        )

        parser.add_argument(
            '--language',
            help='Language code for report and notification language. Default is "en" for English.',
            default='en'
        )

        parser.add_argument(
            '--subsystem',
            metavar="SYSTEM",
            default=None,
            help="""
                Target subsystem in format CLASS:MEMBER:SUBSYSTEM.
                If this argument is omitted reports are generated for all subsystems listed in xroad descriptor file.
            """
        )

        parser.add_argument(
            '--email',
            default=None,
            help="""
                This e-mail address is notified about a new report if the "--subsystem" argument is defined.
                If subsystem is not defined, the e-mail addresses are parsed from xroad descriptor file.
            """
        )

        parser.add_argument(
            '--start-date',
            dest='start_date',
            metavar="DATE",
            help='Report start date in format "YYYY-MM-DD". Default is the first day of the previous month',
            default=start_date_default
        )

        parser.add_argument(
            '--end-date',
            metavar="DATE",
            dest='end_date',
            help='Report end date in format "YYYY-MM-DD". Default is the last day of the previous month',
            default=end_date_default
        )
        return parser.parse_args()
