import logging
import os

appdir = '/srv/app'
x_road_instance = 'sample'

# Anonymizer
anonymizer = {}

anonymizer['field_translations_file'] = 'field_translations.list'
anonymizer['transformers'] = ['default.reduce_request_in_ts_precision', 'default.force_durations_to_integer_range']
anonymizer['threads'] = 1

# MongoDB (anonymizer input) connection parameters
mongo_db = {}

mongo_db['host_address'] = '#NA'
mongo_db['port'] = 27017
mongo_db['auth_db'] = 'auth_db'
mongo_db['user'] = 'anonymizer_' + x_road_instance
mongo_db['password'] = '#NA'
mongo_db['database_name'] = 'query_db_' + x_road_instance
mongo_db['table_name'] = 'clean_data'

mongo_db['state'] = {
    'database_name': 'anonymizer_state_' + x_road_instance,
    'table_name': 'state'
}

# PostgreSQL connection parameters
postgres = {}

postgres['buffer_size'] = 10000
postgres['host_address'] = '#NA'
postgres['port'] = 5432
postgres['database_name'] = 'opendata_' + x_road_instance.lower().replace('-', '_')
postgres['table_name'] = 'logs'
postgres['user'] = 'anonymizer_' + x_road_instance.lower().replace('-', '_')
postgres['readonly_users'] = [
    'interface_' + x_road_instance.lower().replace('-', '_'),
    'networking_' + x_road_instance.lower().replace('-', '_')
]
postgres['password'] = '#NA'

# Hiding rules for removing selected entries altogether
# According to Security Authorities Act [1] §5 the security authorities are the Estonian Internal Security Service and the Estonian Foreign Intelligence Service. Their authorizations are described in chapter 4 (§21 - 35) of the above mentioned act. Based on aspects stated in the State Secrets and Classified Information of Foreign States Act [2] §11 section 3, §7 p 10 and § 8 p 1 and in the Public Information Act [3] §35 section 1 p 1, 31, 51 the X-Road usage statistics of security authorities is considered to be for internal use only. X-Road data that is being published as open data by RIA does not contain information about the security authorities.
# [1] Security Authorities Act https://www.riigiteataja.ee/en/eli/ee/521062017015/consolide/current
# [2] Foreign States Act https://www.riigiteataja.ee/en/eli/ee/519062017007/consolide/current
# [3] Public Information Act https://www.riigiteataja.ee/en/eli/ee/518012016001/consolide/current

hiding_rules = [
    [{'feature': 'clientMemberCode', 'regex': '^(70005938|70000591)$'}],
    [{'feature': 'serviceMemberCode', 'regex': '^(70005938|70000591)$'}],
    [{'feature': 'clientSubsystemCode', 'regex': '^(#NA)$'}],
    [{'feature': 'serviceSubsystemCode', 'regex': '^(#NA)$'}]
]

# Substitutions

substitution_rules = [
    {
        'conditions': [
            {'feature': 'clientXRoadInstance', 'regex': '^XYZ$'},
        ],
        'substitutes': [
            {'feature': 'clientMemberClass', 'value': '#NA'}
        ]
    },
]

field_data_file = 'field_data.yaml'

# Logging and heartbeat parameters
log = {}

log['path'] = os.path.join('{0}/{1}/logs/'.format(appdir, x_road_instance),
                           'log_opendata-anonymizer_{0}.json'.format(x_road_instance))
log['name'] = 'opendata_module - anonymizer'
log['max_file_size'] = 2 * 1024 * 1024
log['backup_count'] = 10
log['level'] = logging.INFO

heartbeat = {}
heartbeat['dir'] = '{0}/{1}/heartbeat'.format(appdir, x_road_instance)
