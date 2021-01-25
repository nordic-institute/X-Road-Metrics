import os

TEST_DIR = os.path.abspath(os.path.dirname(__file__))

anonymizer = {}

anonymizer['field_translations_file'] = os.path.join('field_translations.list')
anonymizer['transformers'] = []
anonymizer['threads'] = 1

mongo_db = {}

postgres = {}
postgres['buffer_size'] = 1000

hiding_rules = []

substitution_rules = []

field_data_file = os.path.join('field_data.yaml')
