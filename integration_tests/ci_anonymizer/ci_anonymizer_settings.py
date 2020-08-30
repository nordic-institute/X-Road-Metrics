import os

x_road_instance = 'ee-dev'

# Anonymizer
anonymizer = {}

anonymizer['field_translations_file'] = 'field_translations.list'
anonymizer['transformers'] = ['default.reduce_request_in_ts_precision']
anonymizer['threads'] = 1

# MongoDB (anonymizer input) connection parameters
mongo_db = {}

mongo_db['host_address'] = 'opmon.ci.kit'
mongo_db['port'] = 27017
mongo_db['auth_db'] = 'auth_db'
mongo_db['user'] = 'ci_test'
mongo_db['password'] = 'ci_test'
mongo_db['database_name'] = 'CI_query_db'
mongo_db['table_name'] = 'clean_data'

# MONGODB_SUFFIX = "PY-INTEGRATION-TEST"
# CORRECTOR_ID = 'corrector_{0}'.format(MONGODB_SUFFIX)

# PostgreSQL connection parameters
postgres = {}

postgres['buffer_size'] = 1000
postgres['host_address'] = 'opmon-opendata.ci.kit'
postgres['port'] = 5432
postgres['database_name'] = 'opendata_ci_test'
postgres['table_name'] = 'logs'
postgres['user'] = 'ci_test'
postgres['readonly_users'] = []
postgres['password'] = 'ci_test'

# Hiding rules for removing selected entries altogether

hiding_rules = [[{'feature': 'clientXRoadInstance', 'regex': '^EE$'},
                {'feature': 'clientMemberClass', 'regex': '^GOV$'},
                {'feature': 'clientMemberCode', 'regex': '^(70005938|70000591)$'}],
                ]

# Substitutions

substitution_rules = [
    {
        'conditions': [
            {'feature': 'clientXRoadInstance', 'regex': '^XYZ$'},
        ],
        'substitutes': [
            {'feature': 'clientMemberClass', 'value': 'X-tee salaklass'}
        ]
    },
]

field_data_file = 'field_data.yaml'

heartbeat_path = os.path.join('/srv/app/{0}/heartbeat'.format(x_road_instance),
                              'opendata-anonymizer.json'.format(x_road_instance))
log_path = os.path.join('/srv/app/{0}/logs/'.format(x_road_instance),
                        'opendata-anonymizer.log'.format(x_road_instance))
