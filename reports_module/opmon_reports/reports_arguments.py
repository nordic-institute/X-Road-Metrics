import argparse

from opmon_reports import time_date_tools
from .settings_parser import OpmonSettingsManager


class OpmonReportsArguments:
    def __init__(self):
        args = self._parse_args()

        self.settings = OpmonSettingsManager(args.profile).settings

        self.subsystem = self._parse_subsystem(args.subsystem)

        self.xroad_instance = self.settings['xroad']['instance']
        self.start_date = args.start_date
        self.end_date = args.end_date
        self.language = args.language

        if self.start_date > self.end_date:
            raise ValueError(f"Start date cannot be after end date.")

    @property
    def member_class(self):
        return self.subsystem['member_class']

    @property
    def member_code(self):
        return self.subsystem['member_code']

    @property
    def subsystem_code(self):
        return self.subsystem['subsystem_code']

    @staticmethod
    def _parse_subsystem(subsystem):
        if subsystem is None:
            return None

        codes = subsystem.split(':')
        if len(codes) != 3:
            raise ValueError(
                "X-Road subsystem must be in format CLASS:MEMBER:SUBSYSTEM. For example ORG:1234:MYSUB")
        keys = ['member_class', 'member_code', 'subsystem_code']
        return dict(zip(keys, codes))

    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser()

        start_date_default = time_date_tools.get_previous_month_first_day().isoformat()
        end_date_default = time_date_tools.get_previous_month_last_day().isoformat()

        parser.add_argument("--profile",
                            metavar="PROFILE",
                            default=None,
                            help="""
                                Optional settings file profile.
                                For example with '--profile PROD' settings_PROD.yaml will be used as settings file.
                                If no profile is defined, settings.yaml will be used by default.
                                Settings file is searched from current working directory and /etc/opmon/reports/
                            """
                            )

        parser.add_argument('--language', dest='language', help='Language ("et"/"en")', default='en')
        parser.add_argument('--subsystem', dest='subsystem', help='Target subsystem in format CLASS:MEMBER:SUBSYSTEM', default=None)
        parser.add_argument('--start_date', dest='start_date', help='StartDate "YYYY-MM-DD". Default is first day of previous month', default=start_date_default)
        parser.add_argument('--end_date', dest='end_date', help='EndDate "YYYY-MM-DD" Default is last day of previous month', default=end_date_default)
        return parser.parse_args()
