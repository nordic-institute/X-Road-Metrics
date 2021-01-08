import operator
import os
import time
from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from . import time_date_tools
from . import tools
from .report_row import ReportRow
from . import constants

matplotlib.use('Agg')
import matplotlib.pyplot as plt

PRODUCED_SERVICES_COLUMN_ORDER = ["SERVICE", "CLIENT", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]
CONSUMED_SERVICES_COLUMN_ORDER = ["PRODUCER", "SERVICE", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]


class ReportManager:
    def __init__(self, reports_arguments, riha_json, log_m, database_manager, translator):
        self.database_manager = database_manager
        self.reports_arguments = reports_arguments
        self.start_date = datetime.strptime(reports_arguments.start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        self.end_date = datetime.strptime(reports_arguments.end_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        self.logger_manager = log_m
        self.translator = translator
        self.riha_json = riha_json

    def is_producer_document(self, document):
        return document["serviceSubsystemCode"] == self.reports_arguments.subsystem_code \
               and document["serviceMemberCode"] == self.reports_arguments.member_code \
               and document["serviceMemberClass"] == self.reports_arguments.member_class \
               and document["serviceXRoadInstance"] == self.reports_arguments.xroad_instance

    def is_client_document(self, document):
        return document["clientSubsystemCode"] == self.reports_arguments.subsystem_code \
               and document["clientMemberCode"] == self.reports_arguments.member_code \
               and document["clientMemberClass"] == self.reports_arguments.member_class \
               and document["clientXRoadInstance"] == self.reports_arguments.xroad_instance

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
        """

        :return:
        """
        # Get start and end date timestamps
        start_time_timestamp = time_date_tools.date_to_timestamp_milliseconds(
            time_date_tools.string_to_date(self.start_date))
        end_time_timestamp = time_date_tools.date_to_timestamp_milliseconds(
            time_date_tools.string_to_date(self.end_date), False)

        # Generate report map
        report_map = dict()

        # Query faulty documents
        faulty_doc_set = self.database_manager.get_faulty_documents(
            self.reports_arguments,
            start_time_timestamp,
            end_time_timestamp
        )
        faulty_docs_found = set()

        matching_docs = self.database_manager.get_matching_documents(
            self.reports_arguments,
            start_time_timestamp,
            end_time_timestamp
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
                    report_map[sorted_service_type][producer][service] = self.do_calculations(doc,
                                                                                              False)  # Count the stuffs
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
                    report_map[sorted_service_type][service][client] = self.do_calculations(doc,
                                                                                            True)  # Count the stuffs
                else:
                    report_map[sorted_service_type][service][client].update_row(doc)

        return report_map

    @staticmethod
    def do_calculations(document, produced_service):
        r_row = ReportRow(produced_service)
        r_row.update_row(document)
        return r_row

    @staticmethod
    def get_min_mean_max(min_val, mean, max_val):
        if min_val is not None:
            min_val = round(min_val)
        avg = None
        if mean[0] is not None:
            avg = round(mean[0] / mean[1])
        if max_val is not None:
            max_val = round(max_val)
        return "{0} / {1} / {2}".format(min_val, avg, max_val)

    def build_producer_document(self, key_name, service_name, dict_data):
        new_dict = dict()
        new_dict[self.translator.get_translation("SERVICE")] = key_name
        new_dict[self.translator.get_translation("CLIENT")] = service_name
        dict_el = dict_data.return_row()
        new_dict[self.translator.get_translation("SUCCEEDED_QUERIES")] = dict_el[0]
        new_dict[self.translator.get_translation("FAILED_QUERIES")] = dict_el[1]
        new_dict[self.translator.get_translation("DURATION_MIN_MEAN_MAX_MS")] = \
            self.get_min_mean_max(dict_el[2], dict_el[3], dict_el[4])
        new_dict[self.translator.get_translation("REQUEST_SIZE_MIN_MEAN_MAX_B")] = \
            self.get_min_mean_max(dict_el[5], dict_el[6], dict_el[7])
        new_dict[self.translator.get_translation("RESPONSE_SIZE_MIN_MEAN_MAX_B")] = \
            self.get_min_mean_max(dict_el[8], dict_el[9], dict_el[10])
        return new_dict

    def build_consumer_document(self, key_name, service_name, dict_data):
        new_dict = dict()
        new_dict[self.translator.get_translation("PRODUCER")] = key_name
        # t_key = list(dict_data.keys())[0]
        new_dict[self.translator.get_translation("SERVICE")] = service_name
        dict_el = dict_data.return_row()
        # dict_el = dict_data[t_key]
        new_dict[self.translator.get_translation("SUCCEEDED_QUERIES")] = dict_el[0]
        new_dict[self.translator.get_translation("FAILED_QUERIES")] = dict_el[1]
        new_dict[self.translator.get_translation("DURATION_MIN_MEAN_MAX_MS")] = \
            self.get_min_mean_max(dict_el[2], dict_el[3], dict_el[4])
        new_dict[self.translator.get_translation("REQUEST_SIZE_MIN_MEAN_MAX_B")] = \
            self.get_min_mean_max(dict_el[5], dict_el[6], dict_el[7])
        new_dict[self.translator.get_translation("RESPONSE_SIZE_MIN_MEAN_MAX_B")] = \
            self.get_min_mean_max(dict_el[8], dict_el[9], dict_el[10])
        return new_dict

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

    def get_name_and_count(self, key_name, dict_data, produced_service, service_name):
        subsystem_code = self.reports_arguments.subsystem_code
        name = f"{subsystem_code}: {key_name}" if produced_service else f"{key_name}: {service_name}"
        t_key = dict_data.return_row()
        count = t_key[0]
        return name, count

    def get_succeeded_top(self, data, produced_service):
        result_dict = dict()
        for key in data:
            for service in data[key]:
                n, c = self.get_name_and_count(key, data[key][service], produced_service, service)
                if c > 0:
                    if n in result_dict:
                        if result_dict[n] < c:
                            result_dict[n] = c
                    else:
                        result_dict[n] = c

        sorted_dict = sorted(result_dict.items(), key=operator.itemgetter(1))
        if len(sorted_dict) < 6:
            return sorted_dict
        else:
            return sorted_dict[-5:]

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

    def create_succeeded_plot(self, data, produced_service, file_name):
        suc_top = self.get_succeeded_top(data, produced_service)

        names = []
        no_of_s = []
        for pair in suc_top:
            names.append(pair[0])
            no_of_s.append(pair[1])

        plot = None
        if len(names) > 0:
            plot = self.create_plot(
                names, no_of_s, self.translator.get_translation('PRODUCED_SERVICES_TOP_COUNT'),
                file_name) if produced_service else self.create_plot(
                names, no_of_s, self.translator.get_translation('CONSUMED_SERVICES_TOP_COUNT'), file_name)
        return plot

    def get_name_and_average(self, key_name, dict_data, produced_service, service):
        subsystem_code = self.reports_arguments.subsystem_code
        name = f"{subsystem_code}: {key_name}" if produced_service else f"{key_name}: {service}"

        dict_el = dict_data.return_row()
        count = round(dict_el[3][0] / dict_el[3][1]) if dict_el[3][0] is not None else None
        return name, count

    def get_duration_top(self, data, produced_service):
        result_dict = dict()
        for key in data:
            for service in data[key]:
                n, c = self.get_name_and_average(key, data[key][service], produced_service, service)
                if c is not None:
                    if n in result_dict:
                        if result_dict[n] < c:
                            result_dict[n] = c
                    else:
                        result_dict[n] = c

        sorted_dict = sorted(result_dict.items(), key=operator.itemgetter(1))
        if len(sorted_dict) < 6:
            return sorted_dict
        else:
            return sorted_dict[-5:]

    def create_duration_plot(self, data, produced_service, file_name):
        dur_top = self.get_duration_top(data, produced_service)
        names = []
        durs = []
        for pair in dur_top:
            names.append(pair[0])
            durs.append(pair[1])

        plot = None
        if len(names) > 0:
            plot = self.create_plot(names, durs, self.translator.get_translation('PRODUCED_SERVICES_TOP_MEAN'),
                                    file_name) if produced_service else self.create_plot(
                names, durs, self.translator.get_translation('CONSUMED_SERVICES_TOP_MEAN'), file_name)
        return plot

    def create_plots(self, report_map, plot_1_path, plot_2_path, plot_3_path, plot_4_path):

        producer_suc_plot = self.create_succeeded_plot(
            report_map['ps'], True, plot_1_path) if 'ps' in report_map else None
        consumer_suc_plot = self.create_succeeded_plot(
            report_map['cs'], False, plot_2_path) if 'cs' in report_map else None
        producer_dur_plot = self.create_duration_plot(
            report_map['ps'], True, plot_3_path) if 'ps' in report_map else None
        consumer_dur_plot = self.create_duration_plot(
            report_map['cs'], False, plot_4_path) if 'cs' in report_map else None

        return producer_suc_plot, consumer_suc_plot, producer_dur_plot, consumer_dur_plot

    def find_document_dictionary(self, member_subsystem_info):
        if member_subsystem_info is None:
            return None
        for doc in member_subsystem_info:
            match = doc['member_code'] == self.reports_arguments.member_code \
                    and doc['subsystem_code'] == self.reports_arguments.subsystem_code \
                    and doc['member_class'] == self.reports_arguments.member_class \
                    and doc['x_road_instance'] == self.reports_arguments.xroad_instance
            if match:
                return doc
        return None

    def get_member_name(self, member_subsystem_info):
        """
        Gets the member name translation from the dictionary file.
        :param member_subsystem_info: The list of dictionaries that contain information about members & subsystems.
        :return: Returns the translation.
        """
        doc = self.find_document_dictionary(member_subsystem_info)
        return doc['member_name'] or ""

    def get_subsystem_name(self, member_subsystem_info):
        """
        Gets the subsystem name translation from the dictionary file.
        :param member_subsystem_info: The list of dictionaries that contain information about members & subsystems.
        :return: Returns the translation.
        """

        doc = self.find_document_dictionary(member_subsystem_info)
        return doc['subsystem_name'][self.reports_arguments.language] or None

    def prepare_template(self, plots, data_frames, creation_time):

        settings = self.reports_arguments.settings['reports']

        # Load RIA images
        language = self.reports_arguments.language
        image_path = settings['image-path']
        image_header_first = constants.RIA_IMAGE_1.format(IMAGE_PATH=image_path, LANGUAGE=language)
        image_header_second = constants.RIA_IMAGE_2.format(IMAGE_PATH=image_path, LANGUAGE=language)
        image_header_third = constants.RIA_IMAGE_3.format(IMAGE_PATH=image_path, LANGUAGE=language)

        # Get member & subsystem name
        member_name_temp = self.get_member_name(self.riha_json)
        subsystem_name_temp = self.get_subsystem_name(self.riha_json)

        subsystem_code = tools.truncate(self.reports_arguments.subsystem_code)
        member_code = tools.truncate(self.reports_arguments.member_code)

        # Setup environment
        env = Environment(loader=FileSystemLoader(settings['html-template']['dir']))

        # Setup template
        template = env.get_template(settings['html-template']['file'])
        template_vars = {
            "title": subsystem_code + "_" + self.start_date + "_" + self.end_date + "_" + creation_time,
            "member_name_translation": self.translator.get_translation('MEMBER_NAME'),
            "member_name": tools.truncate(member_name_temp),
            "subsystem_name_translation": self.translator.get_translation('SUBSYSTEM_NAME'),
            "subsystem_name": tools.truncate(subsystem_name_temp),
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
            "image_header_third": image_header_third,
            "xroadEnv": self.translator.get_translation('X_ROAD_ENV'),
            "xroad_instance": self.reports_arguments.xroad_instance
        }

        # Render the template
        html_out = template.render(template_vars)
        return html_out

    def save_pdf_to_file(self, pdf, creation_time):
        settings = self.reports_arguments.settings['reports']
        output_directory = os.path.join(
            settings['report-path'],
            self.reports_arguments.xroad_instance,
            self.reports_arguments.member_class,
            self.reports_arguments.member_code
        )
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        report_name = "{0}_{1}_{2}_{3}.pdf".format(
            tools.format_string(self.reports_arguments.subsystem_code),
            self.start_date,
            self.end_date,
            creation_time
        )
        report_file = os.path.join(output_directory, report_name)

        HTML(string=pdf).write_pdf(report_file, stylesheets=settings['css-paths'])

        return report_name

    @staticmethod
    def remove_image(image_path):
        try:
            os.remove(image_path)
        except OSError:
            pass

    def generate_report(self):
        start_generate_report = time.time()

        report_map = self.get_documents()
        data_frames = self.create_data_frames(report_map)

        plots = self.create_plots(
            report_map,
            "reports_module/produced_succeeded_plot.png",
            "reports_module/consumed_succeeded_plot.png",
            "reports_module/produced_mean_plot.png",
            "reports_module/consumed_mean_plot.png"
        )

        creation_time = time_date_tools.datetime_to_modified_string(datetime.now())
        template = self.prepare_template(plots, data_frames, creation_time)

        report_name = self.save_pdf_to_file(template, creation_time)
        map(self.remove_image, plots)

        end_generate_report = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_generate_report - start_generate_report))
        self.logger_manager.log_info("reports_info", "generate_report took: {0}".format(total_time))

        return report_name
