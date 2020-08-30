import time

RAW_DATA_COLLECTION = 'raw_messages'
CLEAN_DATA_COLLECTION = 'clean_data'
NOTIFICATION_COLLECTION = 'notification_queue'


class DatabaseManager:
    def __init__(self, mongodb_handler, logger_manager):
        """
        Creates a DatabaseManager object that keeps the MongoDB user credentials inside.
        :param mongodb_handler: MongoDB handler object.
        :param logger_manager: LoggerManager object for logging.
        """
        self.logger_m = logger_manager
        self.mongodb_handler = mongodb_handler

    @staticmethod
    def get_timestamp():
        """
        Returns current timestamp.
        :return: Returns current timestamp.
        """
        return float(time.time())

    def get_matching_documents(self, member_code, subsystem_code, member_class, x_road_instance, start_time, end_time):
        """Query cleaned data for documents based on member_code, subsystem_code, member_class, start_time, end_time.
        :param x_road_instance: The XRoadInstance to be queried.
        :param member_code: The memberCode that needs to be queried, a field in the JSON doc.
        :param subsystem_code: The subsystemCode that needs to be queried, a field in the JSON doc.
        :param member_class: The memberClass that needs to be queried, a field in the JSON doc.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns the cursor that contains the found documents.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # ------------------------------------
            # Producer group
            # ------------------------------------
            # Query matching documents as producer
            query_a = dict()
            query_a["producer.serviceXRoadInstance"] = x_road_instance
            query_a["producer.serviceMemberCode"] = member_code
            query_a["producer.serviceSubsystemCode"] = subsystem_code
            query_a["producer.serviceMemberClass"] = member_class
            query_a["producer.requestInTs"] = {"$gte": start_time, "$lte": end_time}
            # Query matching documents as producer from client field
            query_c = dict()
            query_c["client.serviceXRoadInstance"] = x_road_instance
            query_c["client.serviceMemberCode"] = member_code
            query_c["client.serviceSubsystemCode"] = subsystem_code
            query_c["client.serviceMemberClass"] = member_class
            query_c["producer"] = None
            query_c["client.requestInTs"] = {"$gte": start_time, "$lte": end_time}
            # ------------------------------------
            # Client group
            # ------------------------------------
            # Query matching documents as client
            query_d = dict()
            query_d["client.clientXRoadInstance"] = x_road_instance
            query_d["client.clientMemberCode"] = member_code
            query_d["client.clientSubsystemCode"] = subsystem_code
            query_d["client.clientMemberClass"] = member_class
            query_d["client.requestInTs"] = {"$gte": start_time, "$lte": end_time}
            # Query matching documents as client from producer
            query_b = dict()
            query_b["producer.clientXRoadInstance"] = x_road_instance
            query_b["producer.clientMemberCode"] = member_code
            query_b["producer.clientSubsystemCode"] = subsystem_code
            query_b["producer.clientMemberClass"] = member_class
            query_b["client"] = None
            query_b["producer.requestInTs"] = {"$gte": start_time, "$lte": end_time}

            # Define projection
            projection = dict()
            projection["_id"] = 1
            projection["correctorTime"] = 1
            projection["producerRequestSize"] = 1
            projection["producerDurationProducerView"] = 1
            projection["clientRequestSize"] = 1
            projection["totalDuration"] = 1
            projection["clientResponseSize"] = 1
            projection["producerResponseSize"] = 1
            projection["client.serviceMemberClass"] = 1
            projection["client.succeeded"] = 1
            projection["client.serviceMemberCode"] = 1
            projection["client.requestInTs"] = 1
            projection["client.serviceCode"] = 1
            projection["client.serviceSubsystemCode"] = 1
            projection["client.serviceVersion"] = 1
            projection["client.clientMemberClass"] = 1
            projection["client.serviceXRoadInstance"] = 1
            projection["client.clientXRoadInstance"] = 1
            projection["client.clientMemberCode"] = 1
            projection["client.clientSubsystemCode"] = 1
            projection["client.securityServerType"] = 1
            projection["producer.serviceMemberClass"] = 1
            projection["producer.succeeded"] = 1
            projection["producer.serviceMemberCode"] = 1
            projection["producer.requestInTs"] = 1
            projection["producer.serviceCode"] = 1
            projection["producer.serviceSubsystemCode"] = 1
            projection["producer.serviceVersion"] = 1
            projection["producer.clientMemberClass"] = 1
            projection["producer.serviceXRoadInstance"] = 1
            projection["producer.clientXRoadInstance"] = 1
            projection["producer.clientMemberCode"] = 1
            projection["producer.clientSubsystemCode"] = 1
            projection["producer.securityServerType"] = 1

            queries = [query_a, query_b, query_c, query_d]
            for q in queries:
                for doc in collection.find(q, projection):
                    yield doc
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_matching_documents', '{0}'.format(repr(e)))
            raise e

    def get_faulty_documents(self, member_code, subsystem_code, member_class, x_road_instance, start_time, end_time):
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            query_a = dict()
            query_a["producer.serviceXRoadInstance"] = x_road_instance
            query_a["producer.serviceMemberCode"] = member_code
            query_a["producer.serviceSubsystemCode"] = subsystem_code
            query_a["producer.serviceMemberClass"] = member_class
            query_a["producer.requestInTs"] = {"$gte": start_time, "$lte": end_time}
            query_a["client.clientXRoadInstance"] = x_road_instance
            query_a["client.clientMemberCode"] = member_code
            query_a["client.clientSubsystemCode"] = subsystem_code
            query_a["client.clientMemberClass"] = member_class
            query_a["client.requestInTs"] = {"$gte": start_time, "$lte": end_time}

            query_b = dict()
            query_b["client.serviceXRoadInstance"] = x_road_instance
            query_b["client.serviceMemberCode"] = member_code
            query_b["client.serviceSubsystemCode"] = subsystem_code
            query_b["client.serviceMemberClass"] = member_class
            query_b["client.requestInTs"] = {"$gte": start_time, "$lte": end_time}
            query_b["producer.clientXRoadInstance"] = x_road_instance
            query_b["producer.clientMemberCode"] = member_code
            query_b["producer.clientSubsystemCode"] = subsystem_code
            query_b["producer.clientMemberClass"] = member_class
            query_b["producer.requestInTs"] = {"$gte": start_time, "$lte": end_time}

            projection = dict()
            projection["_id"] = 1

            faulty_set = set()

            queries = [query_a, query_b]
            for q in queries:
                for doc in collection.find(q, projection):
                    faulty_set.add(doc['_id'])

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_matching_documents', '{0}'.format(repr(e)))
            raise e
        return faulty_set

    def get_documents_within_time_frame(self, start_time, end_time):
        """
        Get all the documents for specified time period.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns the list of matching documents.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            cursor = collection.aggregate(
                [
                    {
                        "$match": {
                            "$or": [
                                {
                                    "producer.requestInTs": {
                                        "$gte": start_time,
                                        "$lte": end_time
                                    }
                                },
                                {
                                    "client.requestInTs": {
                                        "$gte": start_time,
                                        "$lte": end_time
                                    }
                                }
                            ]
                        }

                    },
                    {
                        "$group": {
                            "_id": "null",
                            "count": {"$sum": 1}
                        }
                    },
                    {
                        "$project": {
                            "count": 1,
                            "_id": 0
                        }
                    }
                ]
            )

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_documents_within_time_frame', '{0}'.format(repr(e)))
            raise e
        return list(cursor)

    def get_services(self, start_time, end_time):
        """
        Get all the unique services and their representing counts for the specified time frame.
        A service consists of the following values: serviceCode, serviceVersion, serviceMemberCode, serviceMemberClass.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns the list of all the services within specified time frame with their counts.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}
            grouping_criteria = {
                "serviceCode": "$document.serviceCode",
                "serviceVersion": "$document.serviceVersion",
                "serviceMemberCode": "$document.serviceMemberCode",
                "serviceMemberClass": "$document.serviceMemberClass"
            }
            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_services', '{0}'.format(repr(e)))
            raise e
        return list(cursor)

    def get_producers(self, start_time, end_time):
        """
        Get all the unique services and their representing counts for the specified time frame.
        A producer consists of the following values: serviceXRoadInstance, serviceMemberClass, serviceMemberCode.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns the list of all the producers within specified time frame with their counts.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}

            grouping_criteria = {
                "serviceXRoadInstance": "$document.serviceXRoadInstance",
                "serviceMemberClass": "$document.serviceMemberClass",
                "serviceMemberCode": "$document.serviceMemberCode"
            }

            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_producers', '{0}'.format(repr(e)))
            raise e
        return list(cursor)

    def get_service_members(self, start_time, end_time):
        """
        Get all the unique service members and their representing counts for the specified time frame.
        A service member consists of the following values: serviceXRoadInstance, serviceMemberClass, serviceMemberCode.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns the list of all the service members within specified time frame with their counts.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}

            grouping_criteria = {
                "serviceXRoadInstance": "$document.serviceXRoadInstance",
                "serviceMemberClass": "$document.serviceMemberClass",
                "serviceMemberCode": "$document.serviceMemberCode"
            }
            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_service_members', '{0}'.format(repr(e)))
            raise e

        return list(cursor)

    def get_client_members(self, start_time, end_time):
        """
        Get all the unique client members and their representing counts for the specified time frame.
        A client member consists of the following values: clientXRoadInstance, clientMemberClass, clientMemberCode.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns the list of all the client members within specified time frame with their counts.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}

            grouping_criteria = {
                "clientXRoadInstance": "$document.clientXRoadInstance",
                "clientMemberClass": "$document.clientMemberClass",
                "clientMemberCode": "$document.clientMemberCode"
            }
            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_client_members', '{0}'.format(repr(e)))
            raise e

        return list(cursor)

    def get_sec_srv_service_count(self, start_time, end_time):
        """
        Gets all the unique service "securityServerAddress"-es and their counts.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns all the unique service "securityServerAddress"-es and their counts.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}

            # serviceXRoadInstance/serviceMemberClass/serviceMemberCode

            grouping_criteria = {
                "serviceSecurityServerAddress": "$document.serviceSecurityServerAddress"
            }
            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_sec_srv_service_count', '{0}'.format(repr(e)))
            raise e

        return list(cursor)

    def get_sec_srv_client_count(self, start_time, end_time):
        """
        Gets all the unique client "securityServerAddress"-es and their counts.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns all the unique client "securityServerAddress"-es and their counts.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}

            # serviceXRoadInstance/serviceMemberClass/serviceMemberCode

            grouping_criteria = {
                "clientSecurityServerAddress": "$document.clientSecurityServerAddress"
            }
            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_sec_srv_client_count', '{0}'.format(repr(e)))
            raise e

        return list(cursor)

    def get_service_subsystems(self, start_time, end_time):
        """
        Gets a list of matching service side subsystems from the MongoDB for the specified time frame.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns a list of matching service side subsystems.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            # step_matching = {"$match": {"$and": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}

            grouping_criteria = {
                "serviceXRoadInstance": "$document.serviceXRoadInstance",
                "serviceMemberClass": "$document.serviceMemberClass",
                "serviceMemberCode": "$document.serviceMemberCode",
                "serviceSubsystemCode": "$document.serviceSubsystemCode"
            }

            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_service_subsystems', '{0}'.format(repr(e)))
            raise e

        return list(cursor)

    def get_client_subsystems(self, start_time, end_time):
        """
        Gets a list of matching client side subsystems from the MongoDB for the specified time frame.
        :param start_time: The starting timestamp for the query.
        :param end_time: The ending timestamp for the query.
        :return: Returns a list of matching client side subsystems.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            # Step_matching: limit the documents range
            step_matching = {"$match": {"$or": []}}
            # step_matching = {"$match": {"$and": []}}
            matching_condition_producer = {"producer.requestInTs": {"$gte": start_time, "$lte": end_time}}
            matching_condition_client = {"client.requestInTs": {"$gte": start_time, "$lte": end_time}}
            step_matching["$match"]["$or"].append(matching_condition_producer)
            step_matching["$match"]["$or"].append(matching_condition_client)

            # Step_condition: choose client/producer sub_document
            step_condition = {"$project": {"document": {}}}
            step_condition["$project"]["document"]["$cond"] = [{"$ne": ["$client", None]}, "$client", "$producer"]

            # Step_matching_2: Make sure that the request succeeded
            step_matching_2 = {"$match": {"document.succeeded": True}}

            # Step_grouping: group the data by grouping_criteria
            step_grouping = {"$group": {}}

            grouping_criteria = {
                "clientXRoadInstance": "$document.clientXRoadInstance",
                "clientMemberClass": "$document.clientMemberClass",
                "clientMemberCode": "$document.clientMemberCode",
                "clientSubsystemCode": "$document.clientSubsystemCode"
            }

            step_grouping["$group"]["_id"] = grouping_criteria
            step_grouping["$group"]["count"] = {"$sum": 1}

            aggregation_steps = [step_matching, step_condition, step_matching_2, step_grouping]
            cursor = collection.aggregate(aggregation_steps)

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_client_subsystems', '{0}'.format(repr(e)))
            raise e

        return list(cursor)

    def get_all_unique_client_subsystems(self):
        """
        Query cleaned data to get all the unique memberClass/memberCode/subsystemCode pairs and their counts.
        :return: Returns a list of all the unique memberClass/memberCode/subsystemCode pairs and their counts.
        """
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            cursor = collection.aggregate(
                [
                    {
                        "$group": {
                            "_id": {
                                "clientClientMemberCode": "$client.clientMemberCode",
                                "clientClientSubsystemCode": "$client.clientSubsystemCode",
                                "clientServiceMemberCode": "$client.serviceMemberCode",
                                "clientServiceSubsystemCode": "$client.serviceSubsystemCode",
                                "producerClientMemberCode": "$producer.clientMemberCode",
                                "producerClientSubsystemCode": "$producer.clientSubsystemCode",
                                "producerServiceMemberCode": "$producer.serviceMemberCode",
                                "producerServiceSubsystemCode": "$producer.serviceSubsystemCode",
                                "clientClientMemberClass": "$client.clientMemberClass",
                                "clientServiceMemberClass": "$client.serviceMemberClass",
                                "producerClientMemberClass": "$producer.clientMemberClass",
                                "producerServiceMemberClass": "$producer.serviceMemberClass"
                            },
                            "count": {
                                "$sum": 1
                            }
                        }
                    }
                ]
            )

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_all_unique_client_subsystems', '{0}'.format(repr(e)))
            raise e
        return list(cursor)

    def add_notification_to_queue(self, member_code, subsystem_code, member_class, x_road_instance, start_date,
                                  end_date, language, notification_username, report_name, email_info):

        """
        Add notification to the queue (database).
        :param email_info: Emails and receiver names list.
        :param report_name: Name of the report.
        :param notification_username: The username string.
        :param member_code: The memberCode string.
        :param subsystem_code: The subsystemCode string.
        :param member_class: The memberClass string.
        :param x_road_instance: The xRoadInstance string.
        :param start_date: The start_date of the report.
        :param end_date: The end_date of the report.
        :param language: The language of the report.
        :return:
        """
        try:
            db = self.mongodb_handler.get_reports_state_db()
            collection = db[NOTIFICATION_COLLECTION]

            status = "no_email_set_not_sent"
            for email in email_info:
                if email['email'] is not "" and email['email'] is not None:
                    status = 'not_sent'

            document = {
                'member_code': member_code, 'subsystem_code': subsystem_code, 'member_class': member_class,
                'x_road_instance': x_road_instance, 'start_date': str(start_date), 'end_date': str(end_date),
                'language': language, 'status': status, 'insert_timestamp': self.get_timestamp(),
                'sending_timestamp': None, 'user_id': notification_username, 'report_name': report_name,
                'email_info': email_info
            }

            collection.insert_one(document)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.add_notification_to_queue', '{0}'.format(repr(e)))
            raise e

    def get_not_processed_notifications(self, notification_username):
        """
        Gets all the notifications from the queue that have not been sent.
        :param notification_username: The unique identifier per setup.
        :return: Returns a list of unprocessed notifications.
        """
        try:
            db = self.mongodb_handler.get_reports_state_db()
            collection = db[NOTIFICATION_COLLECTION]

            cursor = collection.find({"status": "not_sent", "user_id": notification_username})
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_not_processed_notifications', '{0}'.format(repr(e)))
            raise e

        return list(cursor)

    def mark_as_sent(self, object_id):
        """
        Mark the specified (object_id) notification as done in the queue.
        :param object_id: Notification object_id in the MongoDB.
        :return:
        """
        try:
            db = self.mongodb_handler.get_reports_state_db()
            collection = db[NOTIFICATION_COLLECTION]

            collection.update(
                {
                    "_id": object_id
                },
                {
                    "$set": {
                        "status": "notification_sent",
                        "sending_timestamp": self.get_timestamp(),
                    }
                }
            )
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.mark_as_sent', '{0}'.format(repr(e)))
            raise e

    def mark_as_sent_error(self, object_id, error_message):
        """
        Mark the specified (object_id) notification as not sent in the queue.
        :param error_message: The message to be displayed in the MongoDB.
        :param object_id: Notification object_id in the MongoDB.
        :return:
        """
        try:
            db = self.mongodb_handler.get_reports_state_db()
            collection = db[NOTIFICATION_COLLECTION]

            collection.update(
                {
                    "_id": object_id
                },
                {
                    "$set": {
                        "status": error_message,
                        "sending_timestamp": self.get_timestamp(),
                    }
                }
            )
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.mark_as_sent_error', '{0}'.format(repr(e)))
            raise e
