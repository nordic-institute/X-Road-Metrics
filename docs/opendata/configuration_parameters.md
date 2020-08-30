
| [![Republic of Estonia Information System Authority](../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Opendata module, Configuration file parameters

Following subsections describe all the `settings.py` parameters. 

**Note:** Anonymizer and Interface have different available parameters.

## Anonymizer

### Field translations file

Field translation file defines, how the (nested) field names in MongoDB are mapped to the PostgreSQL database field names.

Entries in MongoDB are "dual", meaning that one entry holds both a *client* log together with the matching *producer* log. Entries in PostgreSQL are singular, meaning that client and producer logs are separated.

The file is also used to determine all the relevant MongoDB fields, meaning that even if it's an identity mapping (field name in MongoDB matches the field name in PostgreSQL), the mapping must exist.

The file must always be located in folder `opendata_module/anonymizer/cfg_lists/`. Default file is called `field_translations.list` and is located at `opendata_module/anonymizer/cfg_lists/field_translations.list`.

```python
anonymizer['field_translations_file'] = 'field_translations.list'
```

The file rows must follow the format

```
mongodb.collections[.nested].path -> postgresql_column_name
```

Example rows from the default file:

```
client.securityServerType -> securityServerType
producer.securityServerType -> securityServerType
totalDuration -> totalDuration
producerDurationProducerView -> producerDurationProducerView
```

### Transformers

Transformers are custom Python functions which take in a singular record with the final Opendata database schema (no "client." or "producer." prefices, postgresql_column_name keys) in the form of Python dictionary and can change one or many values. By default, only a transformer for reducing *requestInTs* accuracy is implemented and installed.

The following statement says that only `opendata_module/anonymizer/transformers/default:reduce_request_in_ts_precision` is applied in the anonymization process. All other custom transformers must be located within the directory `transformers`.

```
anonymizer['transformers'] = ['default.reduce_request_in_ts_precision']
```

The corresponding transformer function removes minute and second precision from *requestInTs* field:

```python
def reduce_request_in_ts_precision(record):
    timestamp = int(record['requestInTs'] / 1000)
    initial_datetime = datetime.fromtimestamp(timestamp)
    altered_datetime = initial_datetime.replace(minute=0, second=0)
    record['requestInTs'] = int(altered_datetime.timestamp())
    return record
```

### Processing threads

Reading from MongoDB is done in the master thread. All the processing and writing is done in parallel among the defined number of threads (subprocesses due to [GIL](https://wiki.python.org/moin/GlobalInterpreterLock "Global Interpreter Lock")). 
It is suggested to set number of threads match with nomber of server processor cores available.

```python
anonymizer['threads'] = 2
```

### MongoDB

MongoDB settings define the connection parameters for an existing MongoDB database.
Please configure following, including 'MODULE_PWD' to match with settings created in [Database module](../database_module.md).

```python
mongo_db['host_address'] = 'opmon'
mongo_db['port'] = 27017
mongo_db['auth_db'] = 'auth_db'
mongo_db['user'] = 'anonymizer_${INSTANCE}'
mongo_db['password'] = 'MODULE_PWD'
mongo_db['database_name'] = 'query_db_${INSTANCE}'
mongo_db['table_name'] = 'clean_data'
```

**Note:** `auth_db` is the table in MongoDB which is responsible for authentication. 
If MongoDB is set up without specific admin on authentication database, *mongo_db['auth_db']* should be the same as *mongo_db['database_name']*.

### PostgreSQL

PostgreSQL settings define the connection parameters for the existing PostgreSQL database (see [Interface and PostgreSQL Node > Installation](interface_postgresql.md#installation).

```
postgres['buffer_size'] = 1000
postgres['host_address'] = 'opmon-opendata'
postgres['port'] = 5432
postgres['database_name'] = '${INSTANCE}_opendata'
postgres['table_name'] = 'logs'
postgres['user'] = '${INSTANCE}_opendata'
postgres['password'] = '${PWD_for_anonymizer_ee_dev}'
```

The odd man is the *buffer_size*, which defines how many records will be processed and sent to the PostgreSQL database by one subprocess at a time.

**Note:** `database_name` and `user` differ between X-Road instances. Table name is always `logs`.

### Hiding rules

Hiding rules allow to define sets of (feature name, feature value regular expression) pairs. 
If all the pairs of any set match a record, the record will not reach in the Opendata database.

The following example defines a single rule, which hides records with 
`clientXRoadInstance=sample` and `clientMemberClass=GOV` and `clientMemberCode=code_1` or `clientMemberCode=code_2`.

```python
hiding_rules = [[{'feature': 'clientXRoadInstance', 'regex': '^sample$'},
                {'feature': 'clientMemberClass', 'regex': '^GOV$'},
                {'feature': 'clientMemberCode', 'regex': '^(code_1|code_2)$'}],
                ]
```

### Substitution rules

Substitution rules allow to hide/alter specific field values with a similar format to hiding rules.

In this manual, `sample` is used as INSTANCE. 
To repeat for another instance, please change `sample` to map your desired instance.

The following example changes "clientMemberClass" values to "#N/A" for all the records of which "clientXRoadInstance=sample". 

```python
substitution_rules = [
    {
        'conditions': [
            {'feature': 'clientXRoadInstance', 'regex': '^sample$'},
        ],
        'substitutes': [
            {'feature': 'clientMemberClass', 'value': '#N/A'}
        ]
    },
]
```

**Note:** *conditions* can have many constraints like in the hiding rules example and *substitutes* can change many values at once when increasing the list size.

### Field data file

Field data file maps descriptions, PostgreSQL data types and optionally agent-specificity to final (PostgreSQL) fields. 

Field data file, just like `opendata_config.py` is duplicated for both Anonymizer (`opendata_module/anonymizer/cfg_lists/field_data.yaml`) and Interface (`opendata_module/interface/cfg_lists/field_data.yaml`). Anonymizer and Interface of the same X-Road instance must have identical field data files.

**Descriptions** are listed in API served gzipped tarball meta files and visible when hovering over GUI's features in preview mode.

**Data types** must be correct and exact PostgreSQL data types, as they are used in automatically creating PostgreSQL database schemas. 

**Agent-specificity** can be defined in order to allow only a single agent ("client","producer") to have a *non-null* value.

```python
field_data_file = 'cfg_lists/field_data.yaml'
```

The following YAML file shows, how "id" and "totalDuration" fields are described. They are stored as bigint and integer and in addition, "totalDuration" is only "available" for "client" logs. Producers also have the "totalDuration" field for data integrity, but their "totalDuration" value is always *null*.

```yaml
fields:
    id:
        description: Unique identifier of the record
        type: bigint
    totalDuration:
        description: Request duration from sending the request to getting a response from the client's perspective
        type: integer
        agent: client
```

## Interface

All the interface-specific settings, such as hosts, static directories etc can be defined in the Django settings file [opendata_module/interface/interface/settings.py](../../opendata_module/interface/instance_configurations/settings_sample.py).