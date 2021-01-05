import argparse
from .settings_parser import OpmonSettingsManager


class OpmonReportsArguments():
    def __init__(self):
        args = self._parse_args()

        self.settings = OpmonSettingsManager(args.profile)

        self.member_code = args.member_code
        self.subsystem_code = args.subsystem_code
        self.member_class = args.member_class
        self.xroad_instance = self.settings['xroad']['instance']
        self.start_date = args.start_date
        self.end_date = args.end_date
        self.language = args.language



    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser()

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

        parser.add_argument('--member_code', dest='member_code', help='MemberCode', required=True)
        parser.add_argument('--subsystem_code', dest='subsystem_code', help='SubsystemCode', default="")
        parser.add_argument('--member_class', dest='member_class', help='MemberClass', required=True)
        parser.add_argument('--start_date', dest='start_date', help='StartDate "YYYY-MM-DD"', required=True)
        parser.add_argument('--end_date', dest='end_date', help='EndDate "YYYY-MM-DD"', required=True)
        parser.add_argument('--language', dest='language', help='Language ("et"/"en")', required=True)
        return parser.parse_args()