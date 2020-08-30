import operator
import os
import time
from datetime import datetime

import matplotlib
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from ..reportslib import time_date_tools
from ..reportslib import tools
from ..reportslib.report_row import ReportRow

matplotlib.use('Agg')
import matplotlib.pyplot as plt

PRODUCED_SERVICES_COLUMN_ORDER = ["SERVICE", "CLIENT", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]
CONSUMED_SERVICES_COLUMN_ORDER = ["PRODUCER", "SERVICE", "SUCCEEDED_QUERIES", "FAILED_QUERIES",
                                  "DURATION_MIN_MEAN_MAX_MS", "REQUEST_SIZE_MIN_MEAN_MAX_B",
                                  "RESPONSE_SIZE_MIN_MEAN_MAX_B"]


class ReportManager:
    def __init__(self, x_road_instance, member_class, member_code, subsystem_code, start_date, end_date,
                 riha_json, log_m, database_manager, language, meta_service_list, translator, html_template,
                 report_path, css_files, ria_file_1, ria_file_2, ria_file_3):
        self.database_manager = database_manager
        self.member_code = member_code
        self.subsystem_code = subsystem_code
        self.member_class = member_class
        self.x_road_instance = x_road_instance
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        self.logger_manager = log_m
        self.meta_services = meta_service_list
        self.translator = translator
        self.language = language
        self.riha_json = riha_json
        self.html_template = html_template
        self.report_path = report_path
        self.css_files = css_files
        self.ria_file_1 = ria_file_1
        self.ria_file_2 = ria_file_2
        self.ria_file_3 = ria_file_3

    @staticmethod
    def is_producer_document(document, subsystem_code, member_code, member_class, xroad_instance):
        """
        :param document:
        :param subsystem_code:
        :param member_code:
        :param member_class:
        :param xroad_instance:
        :return:
        """
        cond_1 = document["serviceSubsystemCode"] == subsystem_code
        cond_2 = document["serviceMemberCode"] == member_code
        cond_3 = document["serviceMemberClass"] == member_class
        cond_4 = document["serviceXRoadInstance"] == xroad_instance
        return cond_1 and cond_2 and cond_3 and cond_4

    @staticmethod
    def is_client_document(document, subsystem_code, member_code, member_class, xroad_instance):
        """
        :param document:
        :param subsystem_code:
        :param member_code:
        :param member_class:
        :param xroad_instance:
        :return:
        """
        cond_1 = document["clientSubsystemCode"] == subsystem_code
        cond_2 = document["clientMemberCode"] == member_code
        cond_3 = document["clientMemberClass"] == member_class
        cond_4 = document["clientXRoadInstance"] == xroad_instance
        return cond_1 and cond_2 and cond_3 and cond_4

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
        """
        :param document:
        :return:
        """
        result = None

        if self.is_producer_document(document, self.subsystem_code, self.member_code, self.member_class,
                                     self.x_road_instance):
            # Definitely producer
            if document["serviceCode"] in self.meta_services:
                result = "pms"
                # Produced meta service
            else:
                result = "ps"
                # Produced service

        if self.is_client_document(document, self.subsystem_code, self.member_code, self.member_class,
                                   self.x_road_instance):
            # Definitely consumer
            if document["serviceCode"] in self.meta_services:
                # Consumed meta service
                result = "cms"
            else:
                # Consumed service
                result = "cs"

        return result

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
        rm = dict()

        # Query faulty documents
        faulty_doc_set = self.database_manager.get_faulty_documents(
            self.member_code, self.subsystem_code, self.member_class, self.x_road_instance, start_time_timestamp,
            end_time_timestamp)
        faulty_docs_found = set()

        # Iterate over all the docs and append to report map
        for doc in self.database_manager.get_matching_documents(self.member_code, self.subsystem_code,
                                                                self.member_class, self.x_road_instance,
                                                                start_time_timestamp, end_time_timestamp):

            if doc['_id'] in faulty_docs_found:
                continue
            if doc['_id'] in faulty_doc_set:
                faulty_docs_found.add(doc['_id'])

            doc = self.reduce_to_plain_json(doc)

            # "ps" / "pms" / "cs" / "cms"
            sorted_service = self.get_service_type(doc)
            if sorted_service not in rm:
                rm[sorted_service] = dict()

            # Get service
            service = self.merge_document_fields(doc, ["serviceCode", "serviceVersion"], "service", ".")

            # Consumer
            if sorted_service == "cs":
                producer = self.merge_document_fields(doc, ["serviceXRoadInstance", "serviceMemberClass",
                                                            "serviceMemberCode", "serviceSubsystemCode"],
                                                      "producer", "/")
                if producer not in rm[sorted_service]:
                    rm[sorted_service][producer] = dict()
                if service not in rm[sorted_service][producer]:
                    rm[sorted_service][producer][service] = self.do_calculations(doc, False)  # Count the stuffs
                else:
                    rm[sorted_service][producer][service].update_row(doc)

            # Consumer Metaservice
            if sorted_service == "cms":
                producer = self.merge_document_fields(doc, ["serviceXRoadInstance", "serviceMemberClass",
                                                            "serviceMemberCode", "serviceSubsystemCode"],
                                                      "producer", "/")
                if producer not in rm[sorted_service]:
                    rm[sorted_service][producer] = dict()
                if service not in rm[sorted_service][producer]:
                    rm[sorted_service][producer][service] = self.do_calculations(doc, False)  # Count the stuffs
                else:
                    rm[sorted_service][producer][service].update_row(doc)

            # Producer
            if sorted_service == "ps":
                if service not in rm[sorted_service]:
                    rm[sorted_service][service] = dict()
                client = self.merge_document_fields(doc,
                                                    ["clientXRoadInstance", "clientMemberClass", "clientMemberCode",
                                                     "clientSubsystemCode"], "client", "/")
                if client not in rm[sorted_service][service]:
                    rm[sorted_service][service][client] = self.do_calculations(doc, True)  # Count the stuffs
                else:
                    rm[sorted_service][service][client].update_row(doc)

            # Producer Metaservice
            if sorted_service == "pms":
                if service not in rm[sorted_service]:
                    rm[sorted_service][service] = dict()
                client = self.merge_document_fields(doc,
                                                    ["clientXRoadInstance", "clientMemberClass",
                                                     "clientMemberCode",
                                                     "clientSubsystemCode"], "client", "/")
                if client not in rm[sorted_service][service]:
                    rm[sorted_service][service][client] = self.do_calculations(doc, True)  # Count the stuffs
                else:
                    rm[sorted_service][service][client].update_row(doc)

        return rm

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
        produced_service_input = report_map['ps'] if ('ps' in report_map and report_map['ps'] is not None) else None
        produced_service_df = self.create_produced_service_df(produced_service_input)
        produced_metaservice_input = report_map['pms'] if (
            'pms' in report_map and report_map['pms'] is not None) else None
        produced_metaservice_df = self.create_produced_service_df(produced_metaservice_input)
        consumed_service_input = report_map['cs'] if ('cs' in report_map and report_map['cs'] is not None) else None
        consumed_service_df = self.create_consumed_service_df(consumed_service_input)
        consumed_metaservice_input = report_map['cms'] if (
            'cms' in report_map and report_map['cms'] is not None) else None
        consumed_metaservice_df = self.create_consumed_service_df(consumed_metaservice_input)

        return produced_service_df, produced_metaservice_df, consumed_service_df, consumed_metaservice_df

    def get_name_and_count(self, key_name, dict_data, produced_service, service_name):
        name = "{0}: {1}".format(
            self.subsystem_code, key_name) if produced_service else "{0}: {1}".format(
            key_name, service_name)
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
        name = "{0}: {1}".format(
            self.subsystem_code, key_name) if produced_service else "{0}: {1}".format(
            key_name, service)
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

    @staticmethod
    def get_member_name(member_code, subsystem_code, member_class, x_road_instance, member_name_dict):
        """
        Gets the member name translation from the dictionary file.
        :param x_road_instance: The xRoadInstance string.
        :param subsystem_code: The subsystemCode string.
        :param member_name_dict: The list of dictionaries that contain information about members & subsystems.
        :param member_code: The member code that the search is based on.
        :param member_class: The member class that the search is based on.
        :return: Returns the translation.
        """
        # Avoid crash
        if member_name_dict is None:
            return ""

        # member_code, subsystem_code, member_class, x_road_instance, member_subsystem_data
        for doc in member_name_dict:
            if doc['member_code'] == member_code and doc['subsystem_code'] == subsystem_code \
                    and doc['member_class'] == member_class and doc['x_road_instance'] == x_road_instance:
                if doc['member_name'] is None:
                    return ""
                else:
                    return doc['member_name']
        return ""

    @staticmethod
    def get_subsystem_name(member_code, subsystem_code, member_class, x_road_instance, language,
                           subsystem_name_dict):
        """
        Gets the subsystem name translation from the dictionary file.
        :param subsystem_name_dict: The list of dictionaries that contain information about members & subsystems.
        :param x_road_instance: The xRoadInstance string.
        :param language: The language string.
        :param member_code: The member code that the search is based on.
        :param subsystem_code: The subsystem code that the search is based on.
        :param member_class: The member class that the search is based on.
        :return: Returns the translation.
        """
        # Avoid crash
        if subsystem_name_dict is None:
            return ""

        # member_code, subsystem_code, member_class, x_road_instance, language, member_subsystem_data
        for doc in subsystem_name_dict:
            if doc['member_code'] == member_code and doc['subsystem_code'] == subsystem_code \
                    and doc['member_class'] == member_class and doc['x_road_instance'] == x_road_instance:
                if doc['subsystem_name'] is None:
                    return ""
                else:
                    return doc['subsystem_name'][language]
        return ""

    def prepare_template(self, html_template_path, member_subsystem_info, plot1, plot2, plot3, plot4, df1, df2, df3,
                         df4, ria_file_path1, ria_file_path2, ria_file_path3, creation_time):
        # Load RIA images
        image_header_first = ria_file_path1
        image_header_second = ria_file_path2
        image_header_third = ria_file_path3

        # Get member & subsystem name
        member_name_temp = self.get_member_name(self.member_code, self.subsystem_code, self.member_class,
                                                self.x_road_instance,
                                                member_subsystem_info)
        subsystem_name_temp = self.get_subsystem_name(self.member_code, self.subsystem_code, self.member_class,
                                                      self.x_road_instance, self.language,
                                                      member_subsystem_info)

        member_name_temp = member_name_temp[:55]
        subsystem_name_temp = subsystem_name_temp[:55]
        subsystem_code = self.subsystem_code[:55] if self.subsystem_code is not None else ""
        member_code = self.member_code[:55] if self.member_code is not None else ""

        # Setup environment
        env = Environment(loader=FileSystemLoader('.'))

        # Setup template
        template = env.get_template(html_template_path)
        template_vars = {
            "title": subsystem_code + "_" + self.start_date + "_" + self.end_date + "_" + creation_time,
            "member_name_translation": self.translator.get_translation('MEMBER_NAME'),
            "member_name": member_name_temp,
            "subsystem_name_translation": self.translator.get_translation('SUBSYSTEM_NAME'),
            "subsystem_name": subsystem_name_temp,
            "memberCode": self.translator.get_translation('MEMBER_CODE'),
            "memberCode_value": member_code,
            "subsystemCode": self.translator.get_translation('SUBSYSTEM_CODE'),
            "subsystemCode_value": subsystem_code,
            "time_period_translation": self.translator.get_translation('REPORT_PERIOD'),
            "time_period": self.start_date + " - " + self.end_date,
            "report_date_translation": self.translator.get_translation('REPORT_DATE'),
            "report_date": creation_time,
            "produced_services_succeeded_plot": plot1,
            "consumed_services_succeeded_plot": plot2,
            "produced_services_mean_plot": plot3,
            "consumed_services_mean_plot": plot4,
            "produced_services": df1.to_html(),
            "produced_metaservices": df2.to_html(),
            "consumed_services": df3.to_html(),
            "consumed_metaservices": df4.to_html(),
            "consumed_metaservices_translation": self.translator.get_translation('CONSUMED_META_SERVICES'),
            "consumed_services_translation": self.translator.get_translation('CONSUMED_SERVICES'),
            "produced_services_translation": self.translator.get_translation('PRODUCED_SERVICES'),
            "produced_metaservices_translation": self.translator.get_translation('PRODUCED_META_SERVICES'),
            "image_header_first": image_header_first,
            "image_header_second": image_header_second,
            "image_header_third": image_header_third,
            "xroadEnv": self.translator.get_translation('X_ROAD_ENV'),
            "xroad_instance": self.x_road_instance
        }

        # Render the template
        html_out = template.render(template_vars)
        return html_out

    def save_pdf_to_file(self, pdf, file_path, style_sheet_path, creation_time):
        output_directory = os.path.join(file_path, self.x_road_instance, self.member_class, self.member_code)
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        report_name = "{0}_{1}_{2}_{3}.pdf".format(
            tools.format_string(self.subsystem_code), self.start_date, self.end_date, creation_time)
        report_file = os.path.join(output_directory, report_name)

        HTML(string=pdf).write_pdf(report_file, stylesheets=style_sheet_path)

        return report_name

    @staticmethod
    def remove_image(image_path):
        if image_path is not None:
            if os.path.isfile(image_path):
                os.remove(image_path)

    def clean_up_temp_images(self, temp_im_1, temp_im_2, temp_im_3, temp_im_4):
        self.remove_image(temp_im_1)
        self.remove_image(temp_im_2)
        self.remove_image(temp_im_3)
        self.remove_image(temp_im_4)

    def generate_report(self):
        start_generate_report = time.time()

        # start_processing_time = time.time()
        report_map = self.get_documents()
        # end_processing_time = time.time()
        # total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        # self.logger_manager.log_info("reports_info", "get_documents took: {0}".format(total_time))
        
        # start_processing_time = time.time()
        df1, df2, df3, df4 = self.create_data_frames(report_map)
        # end_processing_time = time.time()
        # total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        # self.logger_manager.log_info("reports_info", "create_data_frames took: {0}".format(total_time))

        # start_processing_time = time.time()
        plot1, plot2, plot3, plot4 = self.create_plots(
            report_map, "reports_module/produced_succeeded_plot.png", "reports_module/consumed_succeeded_plot.png",
            "reports_module/produced_mean_plot.png", "reports_module/consumed_mean_plot.png")
        # end_processing_time = time.time()
        # total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        # self.logger_manager.log_info("reports_info", "create_plots took: {0}".format(total_time))
        
        # start_processing_time = time.time()
        creation_time = time_date_tools.datetime_to_modified_string(datetime.now())
        template = self.prepare_template(
            self.html_template, self.riha_json, plot1, plot2, plot3, plot4, df1, df2, df3, df4, self.ria_file_1,
            self.ria_file_2, self.ria_file_3, creation_time)
        # end_processing_time = time.time()
        # total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        # self.logger_manager.log_info("reports_info", "prepare_template took: {0}".format(total_time))

        # start_processing_time = time.time()
        report_name = self.save_pdf_to_file(template, self.report_path, self.css_files, creation_time)
        # end_processing_time = time.time()
        # total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        # self.logger_manager.log_info("reports_info", "save_pdf_to_file took: {0}".format(total_time))

        self.clean_up_temp_images(plot1, plot2, plot3, plot4)

        end_generate_report = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_generate_report - start_generate_report))
        self.logger_manager.log_info("reports_info", "generate_report took: {0}".format(total_time))

        return report_name
