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

import operator
import os
import tempfile
import time
from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import weasyprint  # type: ignore

from . import time_date_tools
from . import tools
from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .report_row import ReportRow
from . import constants
from .reports_arguments import OpmonReportsArguments
from .translator import Translator
from .xroad_descriptor import OpmonXroadSubsystemDescriptor

matplotlib.use('Agg')
import matplotlib.pyplot as plt

PRODUCED_SERVICES_COLUMN_ORDER = ["SERVICE", "CLIENT", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]
CONSUMED_SERVICES_COLUMN_ORDER = ["PRODUCER", "SERVICE", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]


class ReportManager:
    def __init__(
            self,
            reports_arguments: OpmonReportsArguments,
            target: OpmonXroadSubsystemDescriptor,
            log_m: LoggerManager,
            database_manager: DatabaseManager,
            translator: Translator
    ):
        log_m.log_info(
            'create_reports_manager',
            f'Prepare reports manager for subsystem "{target.subsystem_code}"'
        )

        self.database_manager = database_manager
        self.reports_arguments = reports_arguments
        self.start_date = datetime.strptime(reports_arguments.start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        self.end_date = datetime.strptime(reports_arguments.end_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        self.logger_manager = log_m
        self.translator = translator
        self.target = target

    def is_producer_document(self, document):
        return document["serviceSubsystemCode"] == self.target.subsystem_code \
            and document["serviceMemberCode"] == self.target.member_code \
            and document["serviceMemberClass"] == self.target.member_class \
            and document["serviceXRoadInstance"] == self.target.xroad_instance

    def is_client_document(self, document):
        return document["clientSubsystemCode"] == self.target.subsystem_code \
            and document["clientMemberCode"] == self.target.member_code \
            and document["clientMemberClass"] == self.target.member_class \
            and document["clientXRoadInstance"] == self.target.xroad_instance

    @staticmethod
    def reduce_to_plain_json(document):
        """
        Brings the nested key-value pairs on top level of the JSON.
        :param document: The input document.
        :return: Returns the document with fixed nesting.
        """
        nested_doc = document.get("client", None)
        if nested_doc is None:
            nested_doc = document.get("producer", None)
        for key in nested_doc:
            document[key] = nested_doc[key]
        document.pop("client", None)
        document.pop("producer", None)

        return document

    def get_service_type(self, document):
        is_meta = document["serviceCode"] in constants.META_SERVICE_LIST

        if self.is_producer_document(document):
            return "pms" if is_meta else "ps"

        if self.is_client_document(document):
            return "cms" if is_meta else "cs"  # Consumed meta service

        return None

    @staticmethod
    def merge_document_fields(document, merged_fields, new_field_name, separator):
        """
        :param document:
        :param merged_fields: A list of fields to be merged.
        :param new_field_name: The name of the new merged field.
        :param separator: The separator between the fields in the new string.
        :return:
        """
        new_field = ""
        for field in merged_fields:
            current_field = document[field] if document[field] is not None else ""
            if current_field != "":
                new_field += str(current_field) + separator
                document.pop(field)

        new_field = new_field[:-len(separator)]
        document[new_field_name] = new_field

        return document[new_field_name]

    def get_documents(self):
        report_map = dict()

        faulty_doc_set = self.database_manager.get_faulty_documents(
            self.target,
            self.reports_arguments.start_time_milliseconds,
            self.reports_arguments.end_time_milliseconds
        )
        faulty_docs_found = set()

        matching_docs = self.database_manager.get_matching_documents(
            self.target,
            self.reports_arguments.start_time_milliseconds,
            self.reports_arguments.end_time_milliseconds
        )

        # Iterate over all the docs and append to report map
        for doc in matching_docs:
            if doc['_id'] in faulty_docs_found:
                continue
            if doc['_id'] in faulty_doc_set:
                faulty_docs_found.add(doc['_id'])

            doc = self.reduce_to_plain_json(doc)

            # "ps" / "pms" / "cs" / "cms"
            sorted_service_type = self.get_service_type(doc)
            if sorted_service_type not in report_map:
                report_map[sorted_service_type] = dict()

            # Get service
            service = self.merge_document_fields(doc, ["serviceCode", "serviceVersion"], "service", ".")

            service_field_names = [
                "serviceXRoadInstance",
                "serviceMemberClass",
                "serviceMemberCode",
                "serviceSubsystemCode"
            ]

            # Consumer or Consumer Metaservice
            if sorted_service_type in ["cs", "cms"]:
                producer = self.merge_document_fields(doc, service_field_names, "producer", "/")
                if producer not in report_map[sorted_service_type]:
                    report_map[sorted_service_type][producer] = dict()
                if service not in report_map[sorted_service_type][producer]:
                    report_map[sorted_service_type][producer][service] = self.do_calculations(doc, False)
                else:
                    report_map[sorted_service_type][producer][service].update_row(doc)

            client_field_names = [
                "clientXRoadInstance",
                "clientMemberClass",
                "clientMemberCode",
                "clientSubsystemCode"
            ]

            # Producer or Producer Metaservice
            if sorted_service_type in ["ps", "pms"]:
                if service not in report_map[sorted_service_type]:
                    report_map[sorted_service_type][service] = dict()
                client = self.merge_document_fields(doc, client_field_names, "client", "/")
                if client not in report_map[sorted_service_type][service]:
                    report_map[sorted_service_type][service][client] = self.do_calculations(doc, True)
                else:
                    report_map[sorted_service_type][service][client].update_row(doc)

        return report_map

    @staticmethod
    def do_calculations(document, produced_service):
        r_row = ReportRow(produced_service)
        r_row.update_row(document)
        return r_row

    @staticmethod
    def get_min_mean_max(min_val, average, max_val):
        return "{0} / {1} / {2}".format(
            round(min_val) if min_val is not None else None,
            average.rounded_average,
            round(max_val) if max_val is not None else None
        )

    def build_producer_document(self, key_name, service_name, dict_data: ReportRow):
        doc = self.build_document_base(dict_data)
        doc.update({
            self.translator.get_translation("SERVICE"): key_name,
            self.translator.get_translation("CLIENT"): service_name,
        })
        return doc

    def build_consumer_document(self, key_name, service_name, dict_data: ReportRow):
        doc = self.build_document_base(dict_data)
        doc.update({
            self.translator.get_translation("PRODUCER"): key_name,
            self.translator.get_translation("SERVICE"): service_name,
        })
        return doc

    def build_document_base(self, dict_data: ReportRow):
        return {
            self.translator.get_translation("SUCCEEDED_QUERIES"): dict_data.succeeded_queries,
            self.translator.get_translation("FAILED_QUERIES"): dict_data.failed_queries,

            self.translator.get_translation("DURATION_MIN_MEAN_MAX_MS"): self.get_min_mean_max(
                dict_data.duration_min, dict_data.duration_avg, dict_data.duration_max),

            self.translator.get_translation("REQUEST_SIZE_MIN_MEAN_MAX_B"): self.get_min_mean_max(
                dict_data.request_max, dict_data.request_avg, dict_data.request_max),

            self.translator.get_translation("RESPONSE_SIZE_MIN_MEAN_MAX_B"): self.get_min_mean_max(
                dict_data.response_min, dict_data.response_avg, dict_data.response_max)
        }

    def get_list_of_produced_services(self, data):
        ps_list = []
        for key in data:
            for service in data[key]:
                temp_dict = self.build_producer_document(key, service, data[key][service])
                ps_list.append(temp_dict)
        return ps_list

    def get_list_of_consumed_services(self, data):
        cs_list = []
        for key in data:
            for service in data[key]:
                temp_dict = self.build_consumer_document(key, service, data[key][service])
                cs_list.append(temp_dict)
        return cs_list

    @staticmethod
    def sort_naive_lowercase(df, columns, ascending=True):
        """
        Sort a DataFrame ignoring case.
        :param df: The input dataframe.
        :param columns: The columns to base the sorting on.
        :param ascending: Ascending or descending.
        :return: Returns the re-sorted dataframe.
        """
        df_temp = pd.DataFrame(index=df.index, columns=columns)

        for kol in columns:
            df_temp[kol] = df[kol].str.lower()
        new_index = df_temp.sort_values(columns, ascending=ascending).index
        return df.reindex(new_index)

    def create_produced_service_df(self, data):
        list_of_formatted_produced_services = self.get_list_of_produced_services(data) if data is not None else None
        produced_services_column_order = [self.translator.get_translation(x) for x in PRODUCED_SERVICES_COLUMN_ORDER]
        df = pd.DataFrame(list_of_formatted_produced_services, columns=produced_services_column_order)
        df = self.sort_naive_lowercase(df, [self.translator.get_translation("SERVICE"),
                                            self.translator.get_translation("CLIENT")], ascending=True)
        df = df.reset_index(drop=True)
        df.index += 1
        return df

    def create_consumed_service_df(self, data):
        list_of_formatted_consumed_services = self.get_list_of_consumed_services(data) if data is not None else None
        consumed_services_column_order = [self.translator.get_translation(x) for x in CONSUMED_SERVICES_COLUMN_ORDER]
        df = pd.DataFrame(list_of_formatted_consumed_services, columns=consumed_services_column_order)
        df = self.sort_naive_lowercase(df, [self.translator.get_translation("PRODUCER"),
                                            self.translator.get_translation("SERVICE")], ascending=True)
        df = df.reset_index(drop=True)
        df.index += 1
        return df

    def create_data_frames(self, report_map):
        produced_service_input = report_map.get('ps')
        produced_service_df = self.create_produced_service_df(produced_service_input)

        produced_metaservice_input = report_map.get('pms')
        produced_metaservice_df = self.create_produced_service_df(produced_metaservice_input)

        consumed_service_input = report_map.get('cs')
        consumed_service_df = self.create_consumed_service_df(consumed_service_input)

        consumed_metaservice_input = report_map.get('cms')
        consumed_metaservice_df = self.create_consumed_service_df(consumed_metaservice_input)

        return produced_service_df, produced_metaservice_df, consumed_service_df, consumed_metaservice_df

    @staticmethod
    def create_plot(list_of_y_values, list_of_x_values, title, file_name):
        """
        Creates a bar plot based on the input values.
        :param list_of_y_values: List of y values (vertical).
        :param list_of_x_values: List of x values (horizontal).
        :param title: The title of the plot.
        :param file_name: The file name of the plot where it will be saved.
        :return: Returns the name of the file.
        """
        plot_height = 0.6 * len(list_of_y_values)
        plot_height = min(plot_height, 3)
        plot_height = max(1.0, plot_height)
        plt.figure(figsize=(15, plot_height))
        people = list_of_y_values
        y_pos = np.arange(len(people))
        performance = list_of_x_values

        plt.barh(y_pos, performance, align='center', height=0.45, color="skyblue")
        plt.yticks(y_pos, people)
        plt.xlim(0, np.max(performance) * 1.1)
        plt.title(title, fontweight='bold')

        for i, v in enumerate(performance):
            plt.text(v, i, str(v), color='black')  # , fontweight='bold'

        plt.tight_layout()
        filename = file_name

        plt.savefig(filename)  # , dpi = 100)
        # plt.clf() # To get rid of having too many open figures
        plt.close('all')

        return filename

    def create_plots(self, report_map, tmp_dir):
        plot_filenames = [
            "produced_succeeded_plot.png",
            "consumed_succeeded_plot.png",
            "produced_mean_plot.png",
            "consumed_mean_plot.png"
        ]

        plot_paths = [os.path.join(tmp_dir, filename) for filename in plot_filenames]

        producer_data = report_map.get('ps')
        consumer_data = report_map.get('cs')

        return (
            self.create_succeeded_plot(producer_data, True, plot_paths[0]),
            self.create_succeeded_plot(consumer_data, False, plot_paths[1]),
            self.create_duration_plot(producer_data, True, plot_paths[2]),
            self.create_duration_plot(consumer_data, False, plot_paths[3])
        )

    def create_succeeded_plot(self, data, produced_service, file_name):
        if data is None:
            return None

        succeeded_top = self.get_succeeded_top(data, produced_service)

        if len(succeeded_top) <= 0:
            return None

        names, success_counts = zip(*succeeded_top)

        title = 'PRODUCED_SERVICES_TOP_COUNT' if produced_service else 'CONSUMED_SERVICES_TOP_COUNT'
        translated_title = self.translator.get_translation(title)
        return self.create_plot(names, success_counts, translated_title, file_name)

    def get_succeeded_top(self, data, produced_service):
        result_dict = dict()

        for key1 in data:
            for key2 in data[key1]:
                count = data[key1][key2].succeeded_queries
                name = f"{self.target.subsystem_code}: {key1}" if produced_service else f"{key1}: {key2}"
                if count <= 0:
                    continue

                if name not in result_dict or result_dict[name] < count:
                    result_dict[name] = count

        sorted_pairs = sorted(result_dict.items(), key=operator.itemgetter(1))
        return sorted_pairs if len(sorted_pairs) < 6 else sorted_pairs[-5:]

    def create_duration_plot(self, data, produced_service, file_name):
        if data is None:
            return None

        top_durations = self.get_duration_top(data, produced_service)

        if len(top_durations) <= 0:
            return None

        names, durations = zip(*top_durations)

        title = 'PRODUCED_SERVICES_TOP_MEAN' if produced_service else 'CONSUMED_SERVICES_TOP_MEAN'
        translated_title = self.translator.get_translation(title)
        return self.create_plot(names, durations, translated_title, file_name)

    def get_duration_top(self, data, produced_service):
        result_dict = dict()
        for key1 in data:
            for key2 in data[key1]:
                duration = data[key1][key2].duration_avg.rounded_average
                name = f"{self.target.subsystem_code}: {key1}" if produced_service else f"{key1}: {key2}"
                if duration is None:
                    continue

                if name not in result_dict or result_dict[name] < duration:
                    result_dict[name] = duration

        sorted_pairs = sorted(result_dict.items(), key=operator.itemgetter(1))
        return sorted_pairs if len(sorted_pairs) < 6 else sorted_pairs[-5:]

    def prepare_template(self, plots, data_frames, creation_time):
        settings = self.reports_arguments.settings['reports']

        # Load RIA images
        language = self.reports_arguments.language
        image_path = settings['image-path']
        image_header_first = constants.LOGO_IMAGE_1.format(IMAGE_PATH=image_path, LANGUAGE=language)
        image_header_second = constants.LOGO_IMAGE_2.format(IMAGE_PATH=image_path, LANGUAGE=language)

        member_name = tools.truncate(self.target.get_member_name())
        subsystem_name = tools.truncate(self.target.get_subsystem_name(language))
        subsystem_code = tools.truncate(self.target.subsystem_code)
        member_code = tools.truncate(self.target.member_code)

        # Setup environment
        env = Environment(loader=FileSystemLoader(settings['html-template']['dir']))

        # Setup template
        template = env.get_template(settings['html-template']['file'])
        template_vars = {
            "title": subsystem_code + "_" + self.start_date + "_" + self.end_date + "_" + creation_time,
            "member_name_translation": self.translator.get_translation('MEMBER_NAME'),
            "member_name": member_name,
            "subsystem_name_translation": self.translator.get_translation('SUBSYSTEM_NAME'),
            "subsystem_name": subsystem_name,
            "memberCode": self.translator.get_translation('MEMBER_CODE'),
            "memberCode_value": member_code,
            "subsystemCode": self.translator.get_translation('SUBSYSTEM_CODE'),
            "subsystemCode_value": subsystem_code,
            "time_period_translation": self.translator.get_translation('REPORT_PERIOD'),
            "time_period": self.start_date + " - " + self.end_date,
            "report_date_translation": self.translator.get_translation('REPORT_DATE'),
            "report_date": creation_time,
            "produced_services_succeeded_plot": plots[0],
            "consumed_services_succeeded_plot": plots[1],
            "produced_services_mean_plot": plots[2],
            "consumed_services_mean_plot": plots[3],
            "produced_services": data_frames[0].to_html(),
            "produced_metaservices": data_frames[1].to_html(),
            "consumed_services": data_frames[2].to_html(),
            "consumed_metaservices": data_frames[3].to_html(),
            "consumed_metaservices_translation": self.translator.get_translation('CONSUMED_META_SERVICES'),
            "consumed_services_translation": self.translator.get_translation('CONSUMED_SERVICES'),
            "produced_services_translation": self.translator.get_translation('PRODUCED_SERVICES'),
            "produced_metaservices_translation": self.translator.get_translation('PRODUCED_META_SERVICES'),
            "image_header_first": image_header_first,
            "image_header_second": image_header_second,
            "xroadEnv": self.translator.get_translation('X_ROAD_ENV'),
            "xroad_instance": self.target.xroad_instance
        }

        # Render the template
        html_out = template.render(template_vars)
        return html_out

    def save_pdf_to_file(self, html: str, creation_time):
        settings = self.reports_arguments.settings['reports']
        output_directory = os.path.join(
            settings['report-path'],
            self.target.xroad_instance,
            self.target.member_class,
            self.target.member_code
        )
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        report_name = "{0}_{1}_{2}_{3}.pdf".format(
            tools.format_string(self.target.subsystem_code),
            self.start_date,
            self.end_date,
            creation_time
        )
        report_file = os.path.join(output_directory, report_name)

        self.logger_manager.log_info('save_pdf_to_file', f'Saving report file "{report_file}".')
        weasyprint.HTML(string=html).write_pdf(report_file, stylesheets=settings['css-paths'])

        return report_name

    def generate_report(self):
        start_generate_report = time.time()

        report_map = self.get_documents()
        data_frames = self.create_data_frames(report_map)

        with tempfile.TemporaryDirectory(prefix="opmon-reports") as tmp:
            plots = self.create_plots(report_map, tmp)

            creation_time = time_date_tools.datetime_to_modified_string(datetime.now())
            template = self.prepare_template(plots, data_frames, creation_time)
            report_name = self.save_pdf_to_file(template, creation_time)

        end_generate_report = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_generate_report - start_generate_report))
        self.logger_manager.log_info("reports_info", "generate_report took: {0}".format(total_time))

        return report_name
