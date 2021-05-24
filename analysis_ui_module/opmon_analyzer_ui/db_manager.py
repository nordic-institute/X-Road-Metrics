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

from pymongo import MongoClient
import pymongo
from datetime import datetime, timedelta
import urllib.parse
from . import constants

operator_map = {"=": "$eq",
                "!=": "$ne",
                "<": "$lt",
                "<=": "$lte",
                ">": "$gt",
                ">=": "$gte"}

FLOAT_PRECISION = 0.001


class IncidentDatabaseManager(object):
    def __init__(self, settings):
        xroad = settings['xroad']['instance']

        self.client = MongoClient(self.get_mongo_uri(settings))
        self.query_db = self.client[f"query_db_{xroad}"]
        self.analyzer_db = self.client[f"analyzer_database_{xroad}"]

    @staticmethod
    def get_mongo_uri(settings):
        user = settings['mongodb']['user']
        password = urllib.parse.quote(settings['mongodb']['password'], safe='')
        host = settings['mongodb']['host']
        return f"mongodb://{user}:{password}@{host}/auth_db"
    
    def load_incident_data(self, start=0, length=25, order_col_name='request_count',
                           order_col_dir="asc", incident_status=["new", "showed"], start_time=None, filter_constraints=None):

        filter_dict = {"incident_status": {"$in": incident_status}}
        if start_time is not None:
            filter_dict["incident_creation_timestamp"] = {"$gte": start_time}
        if filter_constraints is not None:
            for field, op, value, data_type in filter_constraints:
                if field not in filter_dict:
                    filter_dict[field] = {}
                    
                if data_type == 'numeric':
                    try:
                        value = float(value)
                    except(OverflowError, ValueError, TypeError):
                        return {"error_message": "<b>%s:</b> Invalid value." % field}
                    
                    if op == '=':
                        filter_dict[field]["$gte"] = value - FLOAT_PRECISION
                        filter_dict[field]["$lte"] = value + FLOAT_PRECISION
                    
                elif data_type == 'date':
                    value = value.strip()
                    for date_format in constants.accepted_date_formats:
                        try:
                            value = datetime.strptime(value, date_format)
                        except ValueError:
                            pass
                        else:
                            break
                    else:
                        return {"error_message": "<b>%s:</b> Accepted date formats are %s" % (field, constants.accepted_date_formats)}
                    if "%M" in date_format:
                        end_date = value + timedelta(minutes=1)
                    else:
                        end_date = value + timedelta(days=1)
                    filter_dict[field]["$gte"] = value
                    filter_dict[field]["$lte"] = end_date
                    
                else:
                    filter_dict[field][operator_map[op]] = value
                    
        result = self.analyzer_db.incident.find(filter_dict)
        filtered_count = result.count()
        total_count = result.count()  # total count should show the count of incidents after filtering by status
        
        order_col_dir = pymongo.ASCENDING if order_col_dir == "asc" else pymongo.DESCENDING
        result = result.sort(order_col_name, order_col_dir)[start:start + length]
        return {"data": list(result), "total_count": total_count, "filtered_count": filtered_count}
    
    def get_distinct_values(self, field, start_time=None, incident_status=["new", "showed"]):
        filter_dict = {"incident_status": {"$in": incident_status}}
        if start_time is not None:
            filter_dict["incident_creation_timestamp"] = {"$gte": start_time}
        return sorted(self.analyzer_db.incident.distinct(field, filter_dict))
    
    def update_incidents(self, ids, field, value):
        result = self.analyzer_db.incident.update(
            {"_id": {"$in": ids}},
            {"$set": {field: value, 'incident_update_timestamp': datetime.now()}},
            multi=True)
        
        return result['nModified']
    
    def get_request_list(self, incident_id, limit=0):

        result = self.analyzer_db.incident.find({"_id": {"$eq": incident_id}})
        request_ids = result[0]["request_ids"]

        result = self.query_db.clean_data.find({"_id": {"$in": request_ids}}).limit(limit)
        
        return list(result)
