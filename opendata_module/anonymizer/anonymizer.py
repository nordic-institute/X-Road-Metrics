import pkgutil
import importlib
import os
from collections import defaultdict
import re
import yaml
import traceback

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


class Anonymizer(object):

    def __init__(self, reader, writer, config, anonymization_job=None, logger_manager=None):
        self._logger = logger_manager

        self._config = config
        self._reader = reader

        field_translations_file_path = (config.anonymizer['field_translations_file']
                                        if config.anonymizer['field_translations_file'].startswith('/')
                                        else os.path.join(ROOT_DIR, 'cfg_lists', config.anonymizer['field_translations_file']))

        field_data_file_path = (config.field_data_file if config.field_data_file.startswith('/')
                                else os.path.join(ROOT_DIR, 'cfg_lists', config.field_data_file))

        self._allowed_fields = self._get_allowed_fields(field_translations_file_path)

        hiding_rules = self._get_hiding_rules()
        substitution_rules = self._get_substitution_rules()
        transformers = self._get_transformers()

        field_translations = self._get_field_translations(field_translations_file_path)
        field_value_masks = self._get_field_value_masks(field_data_file_path)

        self._anonymization_job = (
            AnonymizationJob(writer, hiding_rules, substitution_rules, transformers,
                             field_translations, field_value_masks, self._logger)
            if not anonymization_job else anonymization_job
        )

    def anonymize(self):
        writer_buffer_size = int(self._config.postgres['buffer_size'])
        record_buffer = []

        batch_start_mongodb_timestamp = None
        batch_end_mongodb_timestamp = None
        last_successful_batch_timestamp = self._reader.last_processed_timestamp

        for record_idx, record in enumerate(self._reader.get_records(self._allowed_fields)):
            if batch_start_mongodb_timestamp is None:
                batch_start_mongodb_timestamp = self._reader.last_processed_timestamp

            record_buffer.append(record)

            if len(record_buffer) >= writer_buffer_size:
                batch_end_mongodb_timestamp = self._reader.last_processed_timestamp
                try:
                    self._anonymization_job.run(record_buffer)
                except:
                    self._logger.log_error('failed_anonymizing_record_batch',
                                           "Record batch with correctorTime within range [{0}, {1}] failed. " +
                                           "Last successful correctorTime was {2}".format(
                                               batch_start_mongodb_timestamp,
                                               batch_end_mongodb_timestamp,
                                               last_successful_batch_timestamp))
                    self._reader.update_last_processed_timestamp(last_successful_batch_timestamp)
                    return record_idx + 1

                record_buffer = []
                self._logger.log_info('record_batch_anonymized',
                                      "{0} records anonymized. correctorTime within range [{1}, {2}]".format(
                                          record_idx + 1, batch_start_mongodb_timestamp, batch_end_mongodb_timestamp))

                batch_start_mongodb_timestamp = None
                last_successful_batch_timestamp = batch_end_mongodb_timestamp

        if record_buffer:
            self._anonymization_job.run(record_buffer)

        try:
            return record_idx + 1
        except:
            return 0    # Got no records from MongoDB

    def anonymize_with_limit(self, log_limit):
        writer_buffer_size = int(self._config.postgres['buffer_size'])
        record_buffer = []

        batch_start_mongodb_timestamp = None
        batch_end_mongodb_timestamp = None
        last_successful_batch_timestamp = self._reader.last_processed_timestamp

        for record_idx, record in enumerate(self._reader.get_records(self._allowed_fields)):
            if record_idx >= log_limit:
                break

            if batch_start_mongodb_timestamp is None:
                batch_start_mongodb_timestamp = self._reader.last_processed_timestamp

            record_buffer.append(record)

            if len(record_buffer) >= writer_buffer_size:
                batch_end_mongodb_timestamp = self._reader.last_processed_timestamp
                try:
                    self._anonymization_job.run(record_buffer)
                except:
                    self._logger.log_error('failed_anonymizing_record_batch',
                                           "Record batch with correctorTime within range [{0}, {1}] failed. " +
                                           "Last successful correctorTime was {2}".format(
                                               batch_start_mongodb_timestamp,
                                               batch_end_mongodb_timestamp,
                                               last_successful_batch_timestamp))
                    self._reader.update_last_processed_timestamp(last_successful_batch_timestamp)
                    return record_idx + 1

                record_buffer = []
                self._logger.log_info('record_batch_anonymized',
                                      "{0} records anonymized. correctorTime within range [{1}, {2}]".format(
                                          record_idx + 1, batch_start_mongodb_timestamp, batch_end_mongodb_timestamp))

                batch_start_mongodb_timestamp = None
                last_successful_batch_timestamp = batch_end_mongodb_timestamp

        if record_buffer:
            self._anonymization_job.run(record_buffer)

        try:
            return record_idx
        except:
            return 0    # Got no records from MongoDB

    def _get_allowed_fields(self, field_translations_file_path):
        try:
            with open(field_translations_file_path) as field_translations_file:
                allowed_fields = [line.strip().split(' -> ')[0] for line in field_translations_file if line.strip()]

            return allowed_fields
        except Exception:
            self._logger.log_error('allowed_fields_parsing_failed',
                                   "Failed to parse allowed fields from field translations file at {0}. ERROR: {1}".format(
                                       os.path.abspath(field_translations_file_path),
                                       traceback.format_exc().replace('\n', '')
                                   ))
            raise

    def _get_hiding_rules(self):
        try:
            rules = []

            for rule in self._config.hiding_rules:
                field_pattern_pairs = [(constraint['feature'], re.compile(constraint['regex'])) for constraint in rule]
                rules.append(field_pattern_pairs)

            return rules
        except Exception:
            self._logger.log_error('hiding_rules_parsing_failed',
                                   "Failed to parse config attribute `hiding_rules`. ERROR: {0}".format(
                                       traceback.format_exc().replace('\n', '')
                                   ))
            raise

    def _get_substitution_rules(self):
        try:
            rules = []

            for rule in self._config.substitution_rules:
                processed_rule = {}
                processed_rule['conditions'] = [(constraint['feature'], re.compile(constraint['regex'])) for constraint in rule['conditions']]
                processed_rule['substitutes'] = rule['substitutes']

                rules.append(processed_rule)

            return rules
        except Exception:
            self._logger.log_error('substitution_rules_parsing_failed',
                                   "Failed to parse config attribute `substitution_rules`. ERROR: {0}".format(
                                       traceback.format_exc().replace('\n', '')
                                   ))
            raise

    def _get_transformers(self):
        try:
            if not self._config.anonymizer['transformers']:
                return []

            try:
                import anonymizer.transformers as transformers
            except:
                import opendata_module.anonymizer.transformers as transformers

            transformer_functions = self._config.anonymizer['transformers']
            transformer_dict = defaultdict(list)

            for transformer_function in transformer_functions:
                function_module, function_name = transformer_function.split('.')
                transformer_dict[function_module].append(function_name)

            transformer_modules = self._get_modules(transformers, [module for module in transformer_dict])

            transformers = [getattr(transformer_modules[transformer_module_name], transformer_function_name)
                            for transformer_module_name in transformer_dict
                            for transformer_function_name in transformer_dict[transformer_module_name]]

            return transformers
        except Exception:
            self._logger.log_error('transformers_parsing_failed',
                                   "Failed to parse config attribute `anonymizer.transformers`.".format(
                                       traceback.format_exc().replace('\n', '')
                                   ))
            raise

    def _get_modules(self, package, modules):
        package_name = package.__name__

        package_prefix = package_name + '.'

        desired_modules = set([package_prefix + module_name for module_name in modules])
        modules = {}

        for importer, module_name, is_package in pkgutil.iter_modules(package.__path__, package_prefix):
            if module_name in desired_modules:
                module = importlib.import_module(module_name, package_name)
                modules[module_name.rsplit('.', 1)[1]] = module

        return modules

    def _get_field_translations(self, field_translations_file_path):
        try:
            translations = {'client': {}, 'producer': {}}

            with open(field_translations_file_path) as field_translations_file:
                for line in field_translations_file:
                    original_name, new_name = line.strip().split(' -> ')
                    original_name_parts = original_name.split('.')

                    if len(original_name_parts) == 1:
                        translations[original_name_parts[0]] = new_name

                    elif len(original_name_parts) == 2:
                        translations[original_name_parts[0]][original_name_parts[1]] = new_name

            return translations
        except Exception:
            self._logger.log_error('field_translations_parsing_failed',
                                   "Failed to parse field translations from {0}. ERROR: {1}".format(
                                       os.path.abspath(field_translations_file_path),
                                       traceback.format_exc().replace('\n', '')
                                   ))
            raise

    def _get_field_value_masks(self, field_data_file_path):
        try:
            masks = {'client': set(), 'producer': set()}
            with open(field_data_file_path) as field_data_file:
                for field_name, field_data in yaml.safe_load(field_data_file)['fields'].items():
                    if 'agent' in field_data:
                        masked_agent = 'client' if field_data['agent'] == 'producer' else 'producer'
                        masks[masked_agent].add(field_name)

            return masks
        except Exception:
            self._logger.log_error('field_value_masks_parsing_failed',
                                   "Failed to parse field value masks from {0}. ERROR: {1}".format(
                                       os.path.abspath(field_data_file_path),
                                       traceback.format_exc().replace('\n', '')
                                   ))
            raise


class AnonymizationJob(object):

    def __init__(self, writer, hiding_rules, substitution_rules, transformers, field_translations, field_value_masks,
                 logger_manager):
        self._writer = writer
        self._hiding_rules = hiding_rules
        self._substitution_rules = substitution_rules
        self._transformers = transformers
        self._field_translations = field_translations
        self._field_value_masks = field_value_masks
        self._logger_manager = logger_manager

    def run(self, dual_records):
        logger = self._logger_manager
        try:
            processed_records = []

            for dual_record in dual_records:
                records = self._get_records(dual_record, logger)

                for record in records:

                    if self._should_be_hidden(record, logger):
                        continue

                    record = self._substitute(record, logger)

                    for transformer in self._transformers:
                        record = transformer(record)

                    processed_records.append(record)

            self._writer.write_records(processed_records)
        except Exception:
            logger.log_error('record_batch_anonymization_failed',
                             "Failed processing a batch of records. ERROR: {0}".format(
                                 traceback.format_exc().replace('\n', '')
                             ))
            raise

    def _should_be_hidden(self, record, logger):
        try:
            for conditions in self._hiding_rules:
                if self._record_matches_conditions(record, conditions):
                    return True

            return False
        except Exception:
            logger.log_error('record_hiding_verification_failed',
                             "Error at verifying whether a record should be hidden using the provided hiding rules. ERROR: {0}".format(
                                 traceback.format_exc().replace('\n', '')
                             ))
            raise

    def _record_matches_conditions(self, record, conditions):
        for field, pattern in conditions:
            if field not in record:
                break

            value = record[field]

            if not pattern.match(str(value)):
                break

        else:
            return True

        return False

    def _substitute(self, record, logger):
        try:
            for substitution_rule in self._substitution_rules:
                if self._record_matches_conditions(record, substitution_rule['conditions']):
                    for substitute in substitution_rule['substitutes']:
                        record[substitute['feature']] = substitute['value']

            return record
        except Exception:
            logger.log_error('applying_substitution_rules_failed',
                             "Error at applying substitution rules to a record. ERROR: {0}".format(
                                 traceback.format_exc().replace('\n', '')
                             ))
            raise

    def _get_records(self, dual_record, logger):
        try:
            records = []
            if 'client' in dual_record:
                record = self._get_agent_record('client', dual_record)
                records.append(record)

            if 'producer' in dual_record:
                record = self._get_agent_record('producer', dual_record)
                records.append(record)

            return records
        except Exception:
            logger.log_error('extracting_single_logs_from_record_failed',
                             "Error at extracting single logs from dual record. ERROR: {0}".format(
                                 traceback.format_exc().replace('\n', '')
                             ))
            raise

    def _get_agent_record(self, agent, dual_record):
        # Translate the record
        agent_translation_table = self._field_translations[agent]
        record = {agent_translation_table[record_key]: dual_record[agent][record_key] for record_key in
                  dual_record[agent]}
        translation_table = self._field_translations

        for record_key, record_value in dual_record.items():
            if record_key not in ['client', 'producer']:
                record[translation_table[record_key]] = record_value

        # Mask the record
        agent_field_value_mask = self._field_value_masks[agent]

        for masked_field in agent_field_value_mask:
            record[masked_field] = None

        return record
