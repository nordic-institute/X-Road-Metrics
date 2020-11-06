from os import listdir
from os.path import isfile, join
import re
from copy import deepcopy

import yaml


class OpmonSettingsManager:
    """
    Class to hold OpMon user settings.

    Can parse settings from a YAML file.
    Settings file is searched from the current working directory and /etc/opmon/collector/.
    Settings file must have extension .yaml or .yml.
    If profile argument is set, settings are fetched from settings_{profile}.yaml.
    If no profile is defined, settings are fetched from settings.yaml.
    """

    def __init__(self, profile=None):
        filename = self._find_settings_file(profile)
        self.settings = self._parse_settings(filename)

    def get(self, keystring):
        """Get settings specified by the keystring, like 'xroad.instance'"""
        keys = list(filter(None, re.split(r'\.|\[|\]', keystring)))
        value = deepcopy(self.settings)
        for k in keys:
            value = value[k if not k.isdigit() else int(k)]

        return value

    def _parse_settings(self, filename):
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)

    @staticmethod
    def _find_settings_file(profile):
        search_paths = ['./', '/etc/opmon/collector/']
        files = []
        for p in search_paths:
            files.extend(OpmonSettingsManager._get_all_files(p))

        settings_files = OpmonSettingsManager._get_settings_files(files, profile)
        return settings_files[0]

    @staticmethod
    def _get_all_files(path):
        try:
            return [join(path, f) for f in listdir(path) if isfile(join(path, f))]
        except FileNotFoundError:
            return []

    @staticmethod
    def _get_settings_files(file_list, profile):
        instance_suffix = '' if profile is None else f'_{profile}'
        pattern = r'.+/settings' + instance_suffix + r'\.(yaml|yml)'

        settings_files = [f for f in file_list if re.match(pattern, f)]
        if len(settings_files) == 0:
            raise FileNotFoundError('Valid settings file not found.')

        return settings_files
