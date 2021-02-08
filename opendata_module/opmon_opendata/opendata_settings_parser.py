import yaml
from opmon_opendata.settings_parser import OpmonSettingsManager


class OpenDataSettingsParser(OpmonSettingsManager):
    def __init__(self, profile=None):
        super().__init__(profile or None)

        with open(self.settings['opendata']['field-data-path']) as field_data_file:
            self.settings['opendata']['field-descriptions'] = yaml.safe_load(field_data_file)['fields']
