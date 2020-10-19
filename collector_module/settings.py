from os import listdir
from os.path import isfile, join
from types import SimpleNamespace
import re

import yaml


class OpmonSettings:
    """
    Class to hold OpMon user settings.

    Can parse settings from a YAML file.
    Settings file is searched from the current working directory and /etc/opmon/collector_module/.
    Settings file must have extension .yaml or .yml.
    If xroad_instance is set, settings file name must be settings_{xroad_instance}.yaml (or .yml).
    If no instance is defined, settings are fetched from a file named settings.yaml (or .yml).
    """

    def __init__(self, xroad_instance=None):
        filename = self._find_settings_file(xroad_instance)
        self.settings = self._parse_settings(filename)

    def _parse_settings(self, filename):
        with open(filename, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)

    def _find_settings_file(self, xroad_instance):
        search_paths = ['./', '/etc/opmon/collector_module/']
        files = []
        for p in search_paths:
            files.extend(self._get_all_files(p))

        settings_files = self._get_settings_files(files, xroad_instance)
        return settings_files[0]

    def _get_all_files(self, path):
        try:
            return [join(path, f) for f in listdir(path) if isfile(join(path, f))]
        except FileNotFoundError:
            pass

    def _get_settings_files(self, file_list, xroad_instance):
        instance_suffix = '' if xroad_instance is None else f'_{xroad_instance}'
        pattern = r'.+/settings' + instance_suffix + r'\.(yaml|yml)'

        settings_files = [f for f in file_list if re.match(pattern, f)]
        if len(settings_files) == 0:
            raise FileNotFoundError('Valid settings file not found.')

        return settings_files
