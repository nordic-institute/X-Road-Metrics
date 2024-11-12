#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#

import errno
import re
from os import listdir
from os.path import isfile, join
from typing import List, Optional

import yaml


class MetricsSettingsManager:
    """
    Class to hold X-Road Metrics user settings.

    Can parse settings from a YAML file.
    Settings file is searched from the current working directory and /etc/xroad-metrics/anonymizer/.
    Settings file must have extension .yaml or .yml.
    If profile argument is set, settings are fetched from settings_{profile}.yaml.
    If no profile is defined, settings are fetched from settings.yaml.
    """

    def __init__(self, profile: Optional[str] = None) -> None:
        filename = self._find_settings_file(profile)
        self.settings = self._parse_settings(filename)

    def _parse_settings(self, filename: str) -> dict:
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)

    @staticmethod
    def _find_settings_file(profile: Optional[str]) -> str:
        search_paths = ['./', '/etc/xroad-metrics/anonymizer/']
        files = []
        for p in search_paths:
            files.extend(MetricsSettingsManager._get_all_files(p))

        settings_files = MetricsSettingsManager._get_settings_files(files, profile)
        return settings_files[0]

    @staticmethod
    def _get_all_files(path: str) -> List[str]:
        try:
            return [join(path, f) for f in listdir(path) if isfile(join(path, f))]
        except FileNotFoundError:
            return []

    @staticmethod
    def _get_settings_files(file_list: List[str], profile: Optional[str]) -> List[str]:
        instance_suffix = '' if profile is None else f'_{profile}'
        pattern = r'^.+/settings' + instance_suffix + r'\.(yaml|yml)$'

        settings_files = [f for f in file_list if re.match(pattern, f)]
        if len(settings_files) == 0:
            raise FileNotFoundError(errno.ENOENT, "Settings file not found", f'settings{instance_suffix}.yaml')

        return settings_files
