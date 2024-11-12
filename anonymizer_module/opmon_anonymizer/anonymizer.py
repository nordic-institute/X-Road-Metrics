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

import os
import re
import yaml

from .transformers import get_enabled_transformers

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


class Anonymizer(object):

    def __init__(
            self,
            reader,
            writer,
            settings,
            logger_manager,
            anonymization_job=None,
    ):
        self._logger = logger_manager

        self._settings = settings
        self._reader = reader

        field_translations_path = settings['anonymizer']['field-translations-file']
        field_data_path = settings['anonymizer']['field-data-file']

        self._allowed_fields = self._get_allowed_fields(field_translations_path, logger_manager)

        hiding_rules = self._get_hiding_rules()
        substitution_rules = self._get_substitution_rules()
        transformers = self._get_transformers()

        field_translations = self._get_field_translations(field_translations_path)
        field_value_masks = self._get_field_value_masks(field_data_path)

        self._anonymization_job = (
            AnonymizationJob(writer, hiding_rules, substitution_rules, transformers,
                             field_translations, field_value_masks, self._logger)
            if not anonymization_job else anonymization_job
        )

    def anonymize(self, log_limit=None):
        writer_buffer_size = int(self._settings['postgres']['buffer-size'])
        record_buffer = []

        batch_start_mongodb_timestamp = None
        last_successful_batch_timestamp = self._reader.last_processed_timestamp

        processed_count = 0

        for record in self._reader.get_records(self._allowed_fields):

            if log_limit is not None and processed_count >= log_limit:
                break

            if batch_start_mongodb_timestamp is None:
                batch_start_mongodb_timestamp = self._reader.last_processed_timestamp

            record_buffer.append(record)

            if len(record_buffer) >= writer_buffer_size:
                batch_end_mongodb_timestamp = self._reader.last_processed_timestamp
                try:
                    self._anonymization_job.run(record_buffer)
                except Exception as e:
                    self._logger.log_exception('failed_anonymizing_record_batch',
                                               f'Record batch with correctorTime within range [{batch_start_mongodb_timestamp}, {batch_end_mongodb_timestamp}] '
                                               'failed. Last successful correctorTime was {last_successful_batch_timestamp}'
                                               f'Error: {str(e)}')
                    self._reader.update_last_processed_timestamp(last_successful_batch_timestamp)
                    return processed_count

                processed_count += len(record_buffer)
                record_buffer = []
                self._logger.log_info(
                    'record_batch_anonymized',
                    f'{processed_count} records anonymized.'
                    + f'correctorTime within range [{batch_start_mongodb_timestamp}, {batch_end_mongodb_timestamp}]'
                )

                batch_start_mongodb_timestamp = None
                last_successful_batch_timestamp = batch_end_mongodb_timestamp

        if record_buffer:
            self._anonymization_job.run(record_buffer)
            processed_count += len(record_buffer)

        return processed_count

    @staticmethod
    def _get_allowed_fields(field_translations_file_path, logger):
        try:
            with open(field_translations_file_path) as field_translations_file:
                allowed_fields = [line.strip().split(' -> ')[0] for line in field_translations_file if line.strip()]

            return allowed_fields
        except Exception as e:
            path = os.path.abspath(field_translations_file_path)
            logger.log_exception('allowed_fields_parsing_failed',
                                 f'Failed to parse allowed fields from field translations file at {path}. Error: {str(e)}')
            raise

    def _get_hiding_rules(self):
        try:
            rules = []

            for rule in self._settings['anonymizer']['hiding-rules']:
                field_pattern_pairs = [(constraint['feature'], re.compile(constraint['regex'])) for constraint in rule]
                rules.append(field_pattern_pairs)

            return rules
        except Exception as e:
            self._logger.log_exception('hiding_rules_parsing_failed',
                                       f'Failed to parse config attribute `hiding_rules`. ERROR: {str(e)}')
            raise

    def _get_substitution_rules(self):
        try:
            rules = []

            for rule in self._settings['anonymizer']['substitution-rules']:
                processed_rule = {
                    'conditions': [
                        (constraint['feature'], re.compile(constraint['regex'])) for constraint in rule['conditions']
                    ],
                    'substitutes': rule['substitutes']
                }
                rules.append(processed_rule)

            return rules
        except Exception as e:
            self._logger.log_exception('substitution_rules_parsing_failed',
                                       f'Failed to parse config attribute `substitution_rules`. ERROR: {str(e)}')
            raise

    def _get_transformers(self):
        """Autobots, transform and roll out!"""
        try:
            return get_enabled_transformers(self._settings['anonymizer']['transformers'])
        except Exception as e:
            self._logger.log_exception('transformers_parsing_failed',
                                       f'Failed to parse config attribute `anonymizer.transformers`. ERROR: {str(e)}')
            raise

    def _get_field_translations(self, field_translations_file_path):
        try:
            translations = {'client': {}, 'producer': {}}
            translations_file_path = os.path.abspath(field_translations_file_path)

            with open(field_translations_file_path) as field_translations_file:
                for line in field_translations_file:
                    original_name, new_name = line.strip().split(' -> ')
                    original_name_parts = original_name.split('.')

                    if len(original_name_parts) == 1:
                        translations[original_name_parts[0]] = new_name

                    elif len(original_name_parts) == 2:
                        translations[original_name_parts[0]][original_name_parts[1]] = new_name

            return translations
        except Exception as e:
            self._logger.log_exception('field_translations_parsing_failed',
                                       f'Failed to parse field translations from {translations_file_path}. ERROR: {str(e)}')
            raise

    def _get_field_value_masks(self, field_data_file_path):
        data_file_path = os.path.abspath(field_data_file_path)
        try:
            masks = {'client': set(), 'producer': set()}
            with open(field_data_file_path) as field_data_file:
                for field_name, field_data in yaml.safe_load(field_data_file)['fields'].items():
                    if 'agent' in field_data:
                        masked_agent = 'client' if field_data['agent'] == 'producer' else 'producer'
                        masks[masked_agent].add(field_name)

            return masks
        except Exception as e:
            self._logger.log_exception('field_value_masks_parsing_failed',
                                       f'Failed to parse field value masks from {data_file_path}. ERROR: {str(e)}')
            raise


class AnonymizationJob(object):

    def __init__(
            self,
            writer,
            hiding_rules,
            substitution_rules,
            transformers,
            field_translations,
            field_value_masks,
            logger_manager
    ):
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

            self._logger_manager.log_info('AnonymizationJob.run',
                                          f'Processing done. Records to write {len(processed_records)}.')
            self._writer.write_records(processed_records)
        except Exception as e:
            logger.log_exception('record_batch_anonymization_failed',
                                 f'Failed processing a batch of records. ERROR: {str(e)}')
            raise

    def _should_be_hidden(self, record, logger):
        try:
            for conditions in self._hiding_rules:
                if self._record_matches_conditions(record, conditions):
                    return True

            return False
        except Exception as e:
            logger.log_exception('record_hiding_verification_failed',
                                 f'Error at verifying whether a record should be hidden using the provided hiding rules. ERROR: {str(e)}')
            raise

    @staticmethod
    def _record_matches_conditions(record, conditions):
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
        except Exception as e:
            logger.log_exception('applying_substitution_rules_failed',
                                 f'Error at applying substitution rules to a record. ERROR: {str(e)}')
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
        except Exception as e:
            logger.log_exception('extracting_single_logs_from_record_failed',
                                 f'Error at extracting single logs from dual record. ERROR: {str(e)}')
            raise

    def _get_agent_record(self, agent, dual_record):
        # Translate the record
        agent_translation_table = self._field_translations[agent]
        record = {
            agent_translation_table[record_key]: dual_record[agent][record_key]
            for record_key in dual_record[agent]
            if record_key in agent_translation_table
        }
        translation_table = self._field_translations

        for record_key, record_value in dual_record.items():
            if record_key not in ['client', 'producer'] and record_key in translation_table:
                record[translation_table[record_key]] = record_value

        # Mask the record
        agent_field_value_mask = self._field_value_masks[agent]

        for masked_field in agent_field_value_mask:
            record[masked_field] = None

        return record
