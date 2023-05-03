#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import os
import traceback

from opmon_anonymizer.anonymizer import AnonymizationJob, Anonymizer


class OpenDataAnonymizer(Anonymizer):

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
        self._allowed_fields = self._get_allowed_fields(field_translations_path, logger_manager)

        hiding_rules = self._get_hiding_rules()
        substitution_rules = self._get_substitution_rules()
        transformers = self._get_transformers()

        self._anonymization_job = (
            OpenDataAnonymizationJob(
                writer, hiding_rules, substitution_rules,
                transformers, self._logger)
            if not anonymization_job else anonymization_job
        )

    def anonymize(self, log_limit=None):
        writer_buffer_size = int(self._settings['postgres']['buffer-size'])
        record_buffer = []

        # TODO
        batch_start_mongodb_timestamp = None
        # last_successful_batch_timestamp = self._reader.last_processed_timestamp
        last_successful_batch_timestamp = 2

        processed_count = 0
        for record in self._reader.get_opendata_records(self._allowed_fields):

            if log_limit is not None and processed_count >= log_limit:
                break

            # if batch_start_mongodb_timestamp is None:
            #     batch_start_mongodb_timestamp = self._reader.last_processed_timestamp

            record_buffer.append(record)

            if len(record_buffer) >= writer_buffer_size:
                # batch_end_mongodb_timestamp = self._reader.last_processed_timestamp
                batch_end_mongodb_timestamp = 1
                try:
                    self._anonymization_job.run(record_buffer)
                except Exception:
                    self._logger.log_error('failed_anonymizing_record_batch',
                                           'Record batch with correctorTime within range [{0}, {1}] failed. '
                                           + 'Last successful correctorTime was {2}'.format(
                                               batch_start_mongodb_timestamp,
                                               batch_end_mongodb_timestamp,
                                               last_successful_batch_timestamp))
                    # self._reader.update_last_processed_timestamp(last_successful_batch_timestamp)
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
                allowed_fields = [line.strip().split(' -> ')[1] for line in field_translations_file if line.strip()]
            allowed_fields = list(set(allowed_fields))
            return allowed_fields
        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            path = os.path.abspath(field_translations_file_path)
            logger.log_error('allowed_fields_parsing_failed',
                             f'Failed to parse allowed fields from field translations file at {path}. ERROR: {trace}')
            raise


class OpenDataAnonymizationJob(AnonymizationJob):
    def __init__(
            self,
            writer,
            hiding_rules,
            substitution_rules,
            transformers,
            logger_manager
    ):
        self._writer = writer
        self._hiding_rules = hiding_rules
        self._substitution_rules = substitution_rules
        self._transformers = transformers
        self._logger_manager = logger_manager

    def run(self, dual_records):
        logger = self._logger_manager
        try:
            processed_records = []
            for record in dual_records:

                if self._should_be_hidden(record, logger):
                    continue

                record = self._substitute(record, logger)

                for transformer in self._transformers:
                    record = transformer(record)

                processed_records.append(record)

            self._logger_manager.log_info('OpenDataAnonymizationJob.run',
                                          f'Processing done. Records to write {len(processed_records)}.')
            self._writer.write_records(processed_records)
        except Exception:
            logger.log_error('record_batch_opendata_anonymization_failed',
                             'Failed processing a batch of records. ERROR: {0}'.format(
                                 traceback.format_exc().replace('\n', '')
                             ))
            raise
