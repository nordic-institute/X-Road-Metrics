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

import time
from typing import Iterable

from .mongodb_handler import MongoDBHandler

RAW_DATA_COLLECTION = 'raw_messages'
CLEAN_DATA_COLLECTION = 'clean_data'
NOTIFICATION_COLLECTION = 'notification_queue'


class DatabaseManager:
    def __init__(self, reports_arguments, logger_manager):
        """
        Creates a DatabaseManager object that keeps the MongoDB user credentials inside.
        :param reports_arguments: OpmonReportsArguments object with command line arguments and parsed settings.
        :param logger_manager: LoggerManager object for logging.
        """
        logger_manager.log_info('create_database_manager', 'Prepare database manager.')
        self.mongodb_handler = MongoDBHandler(reports_arguments.settings['mongodb'], reports_arguments.xroad_instance)
        self.logger_m = logger_manager
        self.arguments = reports_arguments

    @staticmethod
    def get_timestamp():
        """
        Returns current timestamp.
        :return: Returns current timestamp.
        """
        return float(time.time())

    def get_matching_documents(self, target, start_time, end_time):
        """Query cleaned data for documents based on member_code, subsystem_code, member_class, start_time, end_time.
        :param target: OpmonXroadSubsystemDescriptor object to define query scope
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
            query_a = {
                "producer.serviceXRoadInstance": target.xroad_instance,
                "producer.serviceMemberCode": target.member_code,
                "producer.serviceSubsystemCode": target.subsystem_code,
                "producer.serviceMemberClass": target.member_class,
                "producer.requestInTs": {"$gte": start_time, "$lte": end_time}
            }
            # Query matching documents as producer from client field
            query_c = {
                "client.serviceXRoadInstance": target.xroad_instance,
                "client.serviceMemberCode": target.member_code,
                "client.serviceSubsystemCode": target.subsystem_code,
                "client.serviceMemberClass": target.member_class,
                "producer": None,
                "client.requestInTs": {"$gte": start_time, "$lte": end_time}
            }
            # ------------------------------------
            # Client group
            # ------------------------------------
            # Query matching documents as client
            query_d = {
                "client.clientXRoadInstance": target.xroad_instance,
                "client.clientMemberCode": target.member_code,
                "client.clientSubsystemCode": target.subsystem_code,
                "client.clientMemberClass": target.member_class,
                "client.requestInTs": {"$gte": start_time, "$lte": end_time}
            }
            # Query matching documents as client from producer
            query_b = {
                "producer.clientXRoadInstance": target.xroad_instance,
                "producer.clientMemberCode": target.member_code,
                "producer.clientSubsystemCode": target.subsystem_code,
                "producer.clientMemberClass": target.member_class,
                "client": None,
                "producer.requestInTs": {"$gte": start_time, "$lte": end_time}
            }

            # Define projection
            projection = {
                "_id": 1,
                "correctorTime": 1,
                "producerRequestSize": 1,
                "producerDurationProducerView": 1,
                "clientRequestSize": 1,
                "totalDuration": 1,
                "clientResponseSize": 1,
                "producerResponseSize": 1,
                "client.serviceMemberClass": 1,
                "client.succeeded": 1,
                "client.serviceMemberCode": 1,
                "client.requestInTs": 1,
                "client.serviceCode": 1,
                "client.serviceSubsystemCode": 1,
                "client.serviceVersion": 1,
                "client.clientMemberClass": 1,
                "client.serviceXRoadInstance": 1,
                "client.clientXRoadInstance": 1,
                "client.clientMemberCode": 1,
                "client.clientSubsystemCode": 1,
                "client.securityServerType": 1,
                "producer.serviceMemberClass": 1,
                "producer.succeeded": 1,
                "producer.serviceMemberCode": 1,
                "producer.requestInTs": 1,
                "producer.serviceCode": 1,
                "producer.serviceSubsystemCode": 1,
                "producer.serviceVersion": 1,
                "producer.clientMemberClass": 1,
                "producer.serviceXRoadInstance": 1,
                "producer.clientXRoadInstance": 1,
                "producer.clientMemberCode": 1,
                "producer.clientSubsystemCode": 1,
                "producer.securityServerType": 1
            }

            queries = [query_a, query_b, query_c, query_d]
            for q in queries:
                for doc in collection.find(q, projection):
                    yield doc
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_matching_documents', '{0}'.format(repr(e)))
            raise e

    def get_faulty_documents(self, target, start_time, end_time):
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            query_a = {
                "producer.serviceXRoadInstance": target.xroad_instance,
                "producer.serviceMemberCode": target.member_code,
                "producer.serviceSubsystemCode": target.subsystem_code,
                "producer.serviceMemberClass": target.member_class,
                "producer.requestInTs": {"$gte": start_time, "$lte": end_time},
                "client.clientXRoadInstance": target.xroad_instance,
                "client.clientMemberCode": target.member_code,
                "client.clientSubsystemCode": target.subsystem_code,
                "client.clientMemberClass": target.member_class,
                "client.requestInTs": {"$gte": start_time, "$lte": end_time}
            }

            query_b = {
                "client.serviceXRoadInstance": target.xroad_instance,
                "client.serviceMemberCode": target.member_code,
                "client.serviceSubsystemCode": target.subsystem_code,
                "client.serviceMemberClass": target.member_class,
                "client.requestInTs": {"$gte": start_time, "$lte": end_time},
                "producer.clientXRoadInstance": target.xroad_instance,
                "producer.clientMemberCode": target.member_code,
                "producer.clientSubsystemCode": target.subsystem_code,
                "producer.clientMemberClass": target.member_class,
                "producer.requestInTs": {"$gte": start_time, "$lte": end_time}
            }

            faulty_set = set()

            for q in [query_a, query_b]:
                for doc in collection.find(q, {"_id": 1}):
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

    def get_unique_subsystems(self, start_time, end_time):
        try:
            db = self.mongodb_handler.get_query_db()
            collection = db[CLEAN_DATA_COLLECTION]

            cursor = collection.aggregate([
                {
                    "$match": {
                        "client.requestInTs": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "clients": self._build_unique_subsystem_query('client'),
                        "services": self._build_unique_subsystem_query('service')
                    }
                },
                {
                    "$project": {
                        "subsystems": {"$setUnion": ["$clients", "$services"]}
                    }
                }
            ])
            try:
                doc = cursor.next()
                return [s for s in doc['subsystems'] if s is not None]
            except StopIteration:
                return []

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_unique_subsystems', repr(e))
            raise e

    @staticmethod
    def _build_unique_subsystem_query(target):
        return {
            "$addToSet": {
                "$cond": [
                    {"$ne": [f"$client.{target}SubsystemCode", None]},
                    {
                        "x_road_instance": f"$client.{target}XRoadInstance",
                        "member_class": f"$client.{target}MemberClass",
                        "member_code": f"$client.{target}MemberCode",
                        "subsystem_code": f"$client.{target}SubsystemCode"
                    },
                    None
                ],
            }
        }

    def add_notification_to_queue(self, target, report_name, receivers: Iterable[dict]):

        """
        Add notification to the queue (database).
        :param target: target subsystem
        :param report_name: Name of the report.
        :param receivers: List of receiver dictionaries
        :return:
        """
        try:
            db = self.mongodb_handler.get_reports_state_db()
            collection = db[NOTIFICATION_COLLECTION]

            status = "no_email_set_not_sent"

            if any((receiver.get('email') for receiver in receivers)):
                status = 'not_sent'

            document = {
                'member_code': target.member_code,
                'subsystem_code': target.subsystem_code,
                'member_class': target.member_class,
                'x_road_instance': target.xroad_instance,
                'start_date': self.arguments.start_date,
                'end_date': self.arguments.end_date,
                'language': self.arguments.language,
                'status': status,
                'insert_timestamp': self.get_timestamp(),
                'sending_timestamp': None,
                'user_id': self.mongodb_handler.user,  # used to identify notifications that belong to the active
                # settings profile / xroad instance
                'report_name': report_name,
                'email_info': receivers
            }

            collection.insert_one(document)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.add_notification_to_queue', '{0}'.format(repr(e)))
            raise e

    def get_not_processed_notifications(self):
        """
        Gets all the notifications from the queue that have not been sent.
        :return: Returns a list of unprocessed notifications.
        """
        try:
            db = self.mongodb_handler.get_reports_state_db()
            collection = db[NOTIFICATION_COLLECTION]

            cursor = collection.find({"status": "not_sent", "user_id": self.mongodb_handler.user})
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
