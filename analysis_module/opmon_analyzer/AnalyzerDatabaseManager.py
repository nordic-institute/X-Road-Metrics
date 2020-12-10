from pymongo import MongoClient
import pymongo
import pandas as pd
import numpy as np
import sys

pd.options.mode.chained_assignment = None


class AnalyzerDatabaseManager(object):
    
    def __init__(self, db_config, config):
        self._db_config = db_config
        self._config = config
    
    def aggregate_data(self, model_type, agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[],
                       metric=None, threshold=None):
        if model_type == "failed_request_ratio":
            return self._aggregate_data_for_failed_request_ratio_model(agg_minutes=agg_minutes, start_time=start_time,
                                                                       end_time=end_time, ids_to_exclude=ids_to_exclude)
        elif model_type == "duplicate_message_ids":
            return self._aggregate_data_for_duplicate_message_id_model(agg_minutes=agg_minutes, start_time=start_time,
                                                                       end_time=end_time, ids_to_exclude=ids_to_exclude)
        elif model_type == "time_sync_errors":
            return self._aggregate_data_for_time_sync_model(relevant_metric=metric, threshold=threshold,
                                                            agg_minutes=agg_minutes, start_time=start_time, end_time=end_time,
                                                            ids_to_exclude=ids_to_exclude)
        else:
            return None
    
    def aggregate_data_for_historic_averages_model(self, agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[], service_calls=None):
        # create connection
        clean_data = self._get_clean_data_collection()
        
        # nested fields need to be projected (select field from client if,  exists, else from producer)
        project_dict = self._get_clean_data_projection_dict()
            
        # conditions to filter the data before processing
        filter_dict_elems = [{'succeeded': True, 'correctorStatus': 'done'}]
        if len(ids_to_exclude) > 0:
            id_exclude_query = {'_id': {'$nin': ids_to_exclude}}
            filter_dict_elems.append(id_exclude_query)
        if start_time is not None:
            start_time_query = {self._config.timestamp_field: {"$gte": start_time}}
            filter_dict_elems.append(start_time_query)
        if end_time is not None:
            end_time_query = {self._config.timestamp_field: {"$lt": end_time}}
            filter_dict_elems.append(end_time_query)
        if service_calls is not None and len(service_calls) > 0:
            for col in self._config.service_call_fields:
                service_calls.loc[service_calls[col] == "-", col] = None
            service_call_query = {"$or": service_calls.to_dict(orient="records")}
            filter_dict_elems.append(service_call_query)
        if len(filter_dict_elems) == 1:
            filter_dict = filter_dict_elems[0]
        elif len(filter_dict_elems) > 1:
            filter_dict = {"$and": filter_dict_elems}
        
        # set up elements to group by (service call fields and temporal aggregation window)
        group_dict = {col: "$%s" % col for col in self._config.service_call_fields}
        group_dict[self._config.timestamp_field] = {
            "$subtract": [
                "$%s" % self._config.timestamp_field,
                {"$mod": ["$%s" % self._config.timestamp_field, 1000 * 60 * agg_minutes]}
            ]}
        
        res = clean_data.aggregate([
            {'$project': project_dict},
            {'$match': filter_dict},
            {'$group': {
                "_id": group_dict,
                "request_count": {"$sum": 1},
                "mean_request_size": {"$avg": "$requestSize"},
                "mean_response_size": {"$avg": "$responseSize"},
                "mean_client_duration": {"$avg": "$totalDuration"},
                "mean_producer_duration": {"$avg": "$producerDurationProducerView"},
                "request_ids": {"$push": "$_id"}}}],
            allowDiskUse=True, maxTimeMS=14400000)
        
        return self._generate_dataframe(list(res))
    
    def add_first_request_timestamps_from_clean_data(self, data=None):
        
        # create connection
        clean_data = self._get_clean_data_collection()
        
        # nested fields need to be projected (select field from client if,  exists, else from producer)
        project_dict = self._get_clean_data_projection_dict()
            
        # conditions to filter the data before processing
        filter_dict = {'correctorStatus': 'done'}
        if data is not None:
            for col in self._config.service_call_fields:
                data.loc[data[col] == "-", col] = None
            filter_dict["$or"] = data.to_dict(orient="records")
        
        # set up elements to group by (service call fields and temporal aggregation window)
        group_dict = {col: "$%s" % col for col in self._config.service_call_fields}
        
        res = clean_data.aggregate([
            {'$project': project_dict},
            {'$match': filter_dict},
            {'$group': {
                "_id": group_dict,
                self._config.timestamp_field: {"$min": "$%s" % self._config.timestamp_field}}}],
            allowDiskUse=True, maxTimeMS=14400000)
        
        res = list(res)
        if len(res) == 0:
            return
        res = self._generate_dataframe(list(res))
        res = res.sort_values(self._config.timestamp_field, ascending=True).drop_duplicates(self._config.service_call_fields)
        
        # exclude service calls that already exist in the first timestamps table
        existing_first_timestamps = self.get_first_timestamps_for_service_calls()
        if len(existing_first_timestamps) > 0:
            res = res.merge(existing_first_timestamps[self._config.service_call_fields + ["first_request_timestamp"]],
                            on=self._config.service_call_fields, how="left")
            res = res[pd.isnull(res.first_request_timestamp)].drop("first_request_timestamp", axis=1)
        
        res = res.rename(columns={self._config.timestamp_field: "first_request_timestamp"})
        res.first_request_timestamp = pd.to_datetime(res.first_request_timestamp, unit='ms')
        res = res.assign(first_incident_timestamp=None)
        res = res.assign(first_model_retrain_timestamp=None)
        res = res.assign(first_model_train_timestamp=None)
        
        # add new service calls
        scft = self._get_service_call_first_timestamps_collection()
        if len(res) > 0:
            scft.insert_many(res.to_dict('records'))

    def get_request_id_count_from_incidents(self, incident_status=["new", "showed", "normal", "incident", "viewed"],
                                            relevant_anomalous_metrics=None, min_incident_creation_timestamp=None,
                                            max_incident_creation_timestamp=None, service_calls=None,
                                            aggregation_timeunits=None):
        filter_dict_elems = [{"incident_status": {"$in": incident_status}}]
        if relevant_anomalous_metrics is not None:
            filter_dict_elems.append({"anomalous_metric": {"$in": relevant_anomalous_metrics}})
        if aggregation_timeunits is not None:
            filter_dict_elems.append({"aggregation_timeunit": {"$in": aggregation_timeunits}})
        if max_incident_creation_timestamp is not None:
            filter_dict_elems.append({"incident_creation_timestamp": {"$lte": max_incident_creation_timestamp}})
        if min_incident_creation_timestamp is not None:
            filter_dict_elems.append({"incident_creation_timestamp": {"$gte": min_incident_creation_timestamp}})
        if service_calls is not None and len(service_calls) > 0:
            for col in self._config.service_call_fields:
                service_calls.loc[service_calls[col] == "-", col] = None
            service_call_query = {"$or": service_calls.to_dict(orient="records")}
            filter_dict_elems.append(service_call_query)
        if len(filter_dict_elems) == 1:
            filter_dict = filter_dict_elems[0]
        elif len(filter_dict_elems) > 1:
            filter_dict = {"$and": filter_dict_elems}
        incident_collection = self._get_incident_collection()
        result = incident_collection.aggregate(
            [{'$match': filter_dict}, {'$group': {'_id': None, 'count': {"$sum": "$request_count"}}}])
        try:
            request_count = next(result)['count']
        except:
            request_count = 0

        return request_count

    def get_incidents(self, incident_status=["new", "showed", "normal", "incident", "viewed"],
                      relevant_anomalous_metrics=None, min_incident_creation_timestamp=None,
                      max_incident_creation_timestamp=None, service_calls=None,
                      aggregation_timeunits=None):
        filter_dict_elems = [{"incident_status": {"$in": incident_status}}]
        if relevant_anomalous_metrics is not None:
            filter_dict_elems.append({"anomalous_metric": {"$in": relevant_anomalous_metrics}})
        if aggregation_timeunits is not None:
            filter_dict_elems.append({"aggregation_timeunit": {"$in": aggregation_timeunits}})
        if max_incident_creation_timestamp is not None:
            filter_dict_elems.append({"incident_creation_timestamp": {"$lte": max_incident_creation_timestamp}})
        if min_incident_creation_timestamp is not None:
            filter_dict_elems.append({"incident_creation_timestamp": {"$gte": min_incident_creation_timestamp}})
        if service_calls is not None and len(service_calls) > 0:
            for col in self._config.service_call_fields:
                service_calls.loc[service_calls[col] == "-", col] = None
            service_call_query = {"$or": service_calls.to_dict(orient="records")}
            filter_dict_elems.append(service_call_query)
        if len(filter_dict_elems) == 1:
            filter_dict = filter_dict_elems[0]
        elif len(filter_dict_elems) > 1:
            filter_dict = {"$and": filter_dict_elems}
        incident_collection = self._get_incident_collection()
        result = incident_collection.find(filter_dict, {"period_start_time": 1, "period_end_time": 1})
        return list(result)

    def update_first_timestamps(self, field, value, service_calls=None):
        scft = self._get_service_call_first_timestamps_collection()
        scft.update({"$or": service_calls.to_dict(orient="records")}, {"$set": {field: value}}, upsert=False, multi=True)
           
    def update_first_train_retrain_timestamps(self, sc_first_model, sc_second_model, current_time):
        if len(sc_first_model) > 0:
            self.update_first_timestamps(field="first_model_train_timestamp",
                                               value=current_time,
                                               service_calls=sc_first_model[self._config.service_call_fields])

        if len(sc_second_model) > 0:
            self.update_first_timestamps(field="first_model_retrain_timestamp",
                                               value=current_time,
                                               service_calls=sc_second_model[self._config.service_call_fields])
            
    def _aggregate_data_for_failed_request_ratio_model(self, agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[]):
        # create connection
        clean_data = self._get_clean_data_collection()
        
        # nested fields need to be projected (select field from client if,  exists, else from producer)
        project_dict = self._get_clean_data_projection_dict()
            
        filter_dict_elems = [{'correctorStatus': 'done'}]
        # conditions to filter the data before processing
        if len(ids_to_exclude) > 0:
            id_exclude_query = {'_id': {'$nin': ids_to_exclude}}
            filter_dict_elems.append(id_exclude_query)
        if start_time is not None:
            start_time_query = {self._config.timestamp_field: {"$gte": start_time}}
            filter_dict_elems.append(start_time_query)
        if end_time is not None:
            end_time_query = {self._config.timestamp_field: {"$lt": end_time}}
            filter_dict_elems.append(end_time_query)
        if len(filter_dict_elems) == 1:
            filter_dict = filter_dict_elems[0]
        elif len(filter_dict_elems) > 1:
            filter_dict = {"$and": filter_dict_elems}
        else:
            filter_dict = {}
        
        # set up elements to group by (service call fields and temporal aggregation window)
        group_dict = {col: "$%s" % col for col in self._config.service_call_fields}
        group_dict[self._config.timestamp_field] = {
            "$subtract": [
                "$%s" % self._config.timestamp_field,
                {"$mod": ["$%s" % self._config.timestamp_field, 1000 * 60 * agg_minutes]}
            ]}
        group_dict['succeeded'] = '$succeeded'
        
        res = clean_data.aggregate([
            {'$project': project_dict},
            {'$match': filter_dict},
            {'$group': {
                "_id": group_dict,
                'count': {'$sum': 1},
                "request_ids": {"$push": "$_id"}}}],
            allowDiskUse=True, maxTimeMS=14400000)
        
        return self._generate_dataframe(list(res))
    
    def _aggregate_data_for_duplicate_message_id_model(self, agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[]):
        # create connection
        clean_data = self._get_clean_data_collection()
        
        # nested fields need to be projected (select field from client if,  exists, else from producer)
        project_dict = self._get_clean_data_projection_dict()
            
        # conditions to filter the data before processing
        filter_dict_elems = [{'succeeded': True, 'correctorStatus': 'done'}]
        if len(ids_to_exclude) > 0:
            id_exclude_query = {'_id': {'$nin': ids_to_exclude}}
            filter_dict_elems.append(id_exclude_query)
        if start_time is not None:
            start_time_query = {self._config.timestamp_field: {"$gte": start_time}}
            filter_dict_elems.append(start_time_query)
        if end_time is not None:
            end_time_query = {self._config.timestamp_field: {"$lt": end_time}}
            filter_dict_elems.append(end_time_query)
        if len(filter_dict_elems) == 1:
            filter_dict = filter_dict_elems[0]
        elif len(filter_dict_elems) > 1:
            filter_dict = {"$and": filter_dict_elems}
        
        # set up elements to group by (service call fields and temporal aggregation window)
        group_dict = {col: "$%s" % col for col in self._config.service_call_fields}
        group_dict[self._config.timestamp_field] = {
            "$subtract": [
                "$%s" % self._config.timestamp_field,
                {"$mod": ["$%s" % self._config.timestamp_field, 1000 * 60 * agg_minutes]}
            ]}
        group_dict['messageId'] = '$messageId'
        
        res = clean_data.aggregate([
            {'$project': project_dict},
            {'$match': filter_dict},
            {'$group': {"_id": group_dict,
                        'message_id_count': {'$sum': 1},
                        "request_ids": {"$push": "$_id"}}},
            {'$match': {'message_id_count': {"$gt": 1}}}],
            allowDiskUse=True, maxTimeMS=14400000)
        
        return self._generate_dataframe(list(res))
    
    def _aggregate_data_for_time_sync_model(self, relevant_metric, threshold, agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[]):
        # create connection
        clean_data = self._get_clean_data_collection()
        
        # nested fields need to be projected (select field from client if,  exists, else from producer)
        project_dict = self._get_clean_data_projection_dict()
            
        # conditions to filter the data before processing
        filter_dict_elems = [{'succeeded': True, 'correctorStatus': 'done'}]
        if len(ids_to_exclude) > 0:
            id_exclude_query = {'_id': {'$nin': ids_to_exclude}}
            filter_dict_elems.append(id_exclude_query)
        if start_time is not None:
            start_time_query = {self._config.timestamp_field: {"$gte": start_time}}
            filter_dict_elems.append(start_time_query)
        if end_time is not None:
            end_time_query = {self._config.timestamp_field: {"$lt": end_time}}
            filter_dict_elems.append(end_time_query)
        if len(filter_dict_elems) == 1:
            filter_dict = filter_dict_elems[0]
        elif len(filter_dict_elems) > 1:
            filter_dict = {"$and": filter_dict_elems}
        
        # set up elements to group by (service call fields and temporal aggregation window)
        group_dict = {col: "$%s" % col for col in self._config.service_call_fields}
        group_dict[self._config.timestamp_field] = {
            "$subtract": [
                "$%s" % self._config.timestamp_field,
                {"$mod": ["$%s" % self._config.timestamp_field, 1000 * 60 * agg_minutes]}
            ]}
        
        res = clean_data.aggregate([
            {'$project': project_dict},
            {'$match': filter_dict},
            {'$group': {"_id": group_dict,
                        'request_count': {'$sum': 1},
                        "docs": {"$push":
                                 {relevant_metric: "$%s" % relevant_metric,
                                  "id": "$_id"}}}},
            {"$unwind": "$docs"},
            {'$match': {'docs.%s' % relevant_metric: {"$lt": threshold}}},
            {'$group': {"_id": "$_id",
                        'erroneous_count': {'$sum': 1},
                        'avg_erroneous_diff': {'$avg': '$docs.%s' % relevant_metric},
                        "request_count": {"$first": "$request_count"},
                        "request_ids": {"$push": "$docs.id"}}}

        ], allowDiskUse=True, maxTimeMS=14400000)
        
        return self._generate_dataframe(list(res))

    def get_request_ids_from_incidents(self, incident_status=["new", "showed", "normal", "incident", "viewed"],
                                       relevant_anomalous_metrics=None, min_incident_creation_timestamp=None,
                                       max_incident_creation_timestamp=None, service_calls=None,
                                       aggregation_timeunits=None):
        filter_dict_elems = [{"incident_status": {"$in": incident_status}}]
        if relevant_anomalous_metrics is not None:
            filter_dict_elems.append({"anomalous_metric": {"$in": relevant_anomalous_metrics}})
        if aggregation_timeunits is not None:
            filter_dict_elems.append({"aggregation_timeunit": {"$in": aggregation_timeunits}})
        if max_incident_creation_timestamp is not None:
            filter_dict_elems.append({"incident_creation_timestamp": {"$lte": max_incident_creation_timestamp}})
        if min_incident_creation_timestamp is not None:
            filter_dict_elems.append({"incident_creation_timestamp": {"$gte": min_incident_creation_timestamp}})
        if service_calls is not None and len(service_calls) > 0:
            for col in self._config.service_call_fields:
                service_calls.loc[service_calls[col] == "-", col] = None
            service_call_query = {"$or": service_calls.to_dict(orient="records")}
            filter_dict_elems.append(service_call_query)
        if len(filter_dict_elems) == 1:
            filter_dict = filter_dict_elems[0]
        elif len(filter_dict_elems) > 1:
            filter_dict = {"$and": filter_dict_elems}
        incident_collection = self._get_incident_collection()
        request_ids = incident_collection.distinct("request_ids", filter_dict)
        return request_ids
    
    def delete_incidents(self, field=None, value=None):
        incident_collection = self._get_incident_collection()
        if field is None or value is None:
            incident_collection.delete_many({})
        else:
            incident_collection.delete_many({field: value})
        
    def insert_incidents(self, dt_incidents):
        incident_collection = self._get_incident_collection()
        incident_collection.insert_many(dt_incidents.to_dict('records'))
    
    def get_timestamp(self, ts_type, model_type):
        ts_collection = self._get_incident_timestamp_collection()
        ts = ts_collection.find_one({"type": ts_type, "model": model_type})
        if ts:
            return ts["timestamp"]
        return ts
    
    def load_model(self, model_name, version=None):
        incident_model_collection = self._get_incident_model_collection()
        
        filter_dict = {"model_name": model_name}
        if version is not None:
            filter_dict["version"] = version
        result = incident_model_collection.find(filter_dict)
        return pd.DataFrame(list(result)).drop("_id", axis=1)
    
    def save_model(self, df, delete_old_version=True):
        incident_model_collection = self._get_incident_model_collection()
        
        df = df.to_dict('records')
        
        if delete_old_version and len(df) > 0:
            model_name = df[0]["model_name"]
            incident_model_collection.delete_many({"model_name": model_name})
            
        incident_model_collection.insert_many(df)
    
    def set_timestamp(self, ts_type, model_type, value):
        ts_collection = self._get_incident_timestamp_collection()
        ts_collection.update({"type": ts_type, "model": model_type},
                             {"type": ts_type, "model": model_type, "timestamp": value},
                             upsert=True)
        
    def get_first_timestamps_for_service_calls(self):
        scft = self._get_service_call_first_timestamps_collection()
        results = list(scft.find())
        if len(results) == 0:
            return pd.DataFrame()
        data = pd.DataFrame(results).drop("_id", axis=1)
        for col in ["first_request_timestamp", "first_model_train_timestamp", "first_incident_timestamp",
                    "first_model_retrain_timestamp"]:
            data.loc[:, col] = pd.to_datetime(data.loc[:, col])
        return data
    
    def get_service_calls_for_train_stages(self, time_first_model, time_second_model):
        first_timestamps = self.get_first_timestamps_for_service_calls()
        
        if len(first_timestamps) == 0:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
        first_model_to_be_trained = first_timestamps[(pd.isnull(first_timestamps.first_model_train_timestamp)) &
                                                     (first_timestamps.first_request_timestamp <= time_first_model)]
        model_to_be_retrained = first_timestamps[(pd.isnull(first_timestamps.first_model_retrain_timestamp)) &
                                                 (first_timestamps.first_incident_timestamp <= time_second_model)]
        first_timestamps = first_timestamps[~pd.isnull(first_timestamps.first_model_retrain_timestamp)]
    
        return first_timestamps, first_model_to_be_trained, model_to_be_retrained
   
    def get_service_calls_for_transform_stages(self):
        first_timestamps = self.get_first_timestamps_for_service_calls()
        first_incidents_to_be_reported = first_timestamps[(pd.isnull(first_timestamps.first_incident_timestamp)) &
                                                          (~pd.isnull(first_timestamps.first_model_train_timestamp))]
        regular_service_calls = first_timestamps[~pd.isnull(first_timestamps.first_incident_timestamp)]
        return regular_service_calls, first_incidents_to_be_reported

    def get_data_for_train_stages(self, sc_regular, sc_first_model, sc_second_model, relevant_anomalous_metrics,
                                  max_incident_creation_timestamp, last_fit_timestamp, agg_minutes,
                                  max_request_timestamp,
                                  min_incident_creation_timestamp=None, aggregation_timeunits=None):

        # ask count of ids to exclude
        n_ids_to_exclude = self.get_request_id_count_from_incidents(
            incident_status=["incident"],
            relevant_anomalous_metrics=relevant_anomalous_metrics,
            max_incident_creation_timestamp=max_incident_creation_timestamp,
            min_incident_creation_timestamp=min_incident_creation_timestamp,
            aggregation_timeunits=aggregation_timeunits)

        # make the timestamps correspond to the millisecond format
        if max_request_timestamp is not None:
            max_request_timestamp = max_request_timestamp.timestamp() * 1000
        if last_fit_timestamp is not None:
            last_fit_timestamp = last_fit_timestamp.timestamp() * 1000

        data_regular = pd.DataFrame()
        data_first_train = pd.DataFrame()
        data_first_retrain = pd.DataFrame()

        # for the first-time training, don't exclude anything
        if len(sc_first_model) > 0:
            if len(sc_first_model) > 100:
                data_first_train = self.aggregate_data_for_historic_averages_model(agg_minutes=agg_minutes,
                                                                                   end_time=max_request_timestamp)
                if len(data_first_train) > 0:
                    data_first_train = data_first_train.merge(sc_first_model[self._config.service_call_fields])
            else:
                data_first_train = self.aggregate_data_for_historic_averages_model(
                    agg_minutes=agg_minutes,
                    end_time=max_request_timestamp,
                    service_calls=sc_first_model[self._config.service_call_fields])

        if n_ids_to_exclude < 1000000:
            # exclude requests that are part of a "true" incident
            ids_to_exclude = self.get_request_ids_from_incidents(
                incident_status=["incident"],
                relevant_anomalous_metrics=relevant_anomalous_metrics,
                max_incident_creation_timestamp=max_incident_creation_timestamp,
                min_incident_creation_timestamp=min_incident_creation_timestamp,
                aggregation_timeunits=aggregation_timeunits)

            # for the second model, exclude queries that were marked as "incident" after the first training,
            # but don't limit the start time
            if len(sc_second_model) > 0:
                if len(sc_second_model) > 100:
                    data_first_retrain = self.aggregate_data_for_historic_averages_model(agg_minutes=agg_minutes,
                                                                                         end_time=max_request_timestamp,
                                                                                         ids_to_exclude=ids_to_exclude)
                    if len(data_first_retrain) > 0:
                        data_first_retrain = data_first_retrain.merge(
                            sc_second_model[self._config.service_call_fields])
                else:
                    data_first_retrain = self.aggregate_data_for_historic_averages_model(
                        agg_minutes=agg_minutes,
                        service_calls=sc_second_model[self._config.service_call_fields],
                        end_time=max_request_timestamp,
                        ids_to_exclude=ids_to_exclude)

            # for regular training, exclude the incidents and limit the start time
            if len(sc_regular) > 0:
                data_regular = self.aggregate_data_for_historic_averages_model(
                    agg_minutes=agg_minutes,
                    start_time=last_fit_timestamp,
                    end_time=max_request_timestamp,
                    ids_to_exclude=ids_to_exclude)
                if len(data_regular) > 0:
                    data_regular = data_regular.merge(sc_regular[self._config.service_call_fields])
        else:
            for sc in sc_second_model:
                sc = sc[self._config.service_call_fields]
                n_ids_to_exclude = self.get_request_id_count_from_incidents(
                    incident_status=["incident"],
                    relevant_anomalous_metrics=relevant_anomalous_metrics,
                    max_incident_creation_timestamp=max_incident_creation_timestamp,
                    min_incident_creation_timestamp=min_incident_creation_timestamp, service_calls=[sc],
                    aggregation_timeunits=aggregation_timeunits)

                if n_ids_to_exclude < 1000000:
                    # exclude requests that are part of a "true" incident
                    ids_to_exclude = self.get_request_ids_from_incidents(
                        incident_status=["incident"],
                        relevant_anomalous_metrics=relevant_anomalous_metrics,
                        max_incident_creation_timestamp=max_incident_creation_timestamp,
                        min_incident_creation_timestamp=min_incident_creation_timestamp, service_calls=[sc],
                        aggregation_timeunits=aggregation_timeunits)

                    data_first_retrain_current = self.aggregate_data_for_historic_averages_model(
                        agg_minutes=agg_minutes,
                        service_calls=[sc],
                        end_time=max_request_timestamp,
                        ids_to_exclude=ids_to_exclude)
                    data_first_retrain = pd.concat([data_first_retrain, data_first_retrain_current], axis=0)
                else:  # iterate by every incident for this service call
                    incidents_current = self.get_incidents(incident_status=["incident"],
                                                           relevant_anomalous_metrics=relevant_anomalous_metrics,
                                                           max_incident_creation_timestamp=max_incident_creation_timestamp,
                                                           min_incident_creation_timestamp=min_incident_creation_timestamp,
                                                           service_calls=[sc],
                                                           aggregation_timeunits=aggregation_timeunits)

                    last_start_time = None
                    for idd, period_start_time, period_end_time in incidents_current:
                        data_first_retrain_current = self.aggregate_data_for_historic_averages_model(
                            agg_minutes=agg_minutes,
                            service_calls=[sc],
                            start_time=last_start_time,
                            end_time=period_start_time)
                        data_first_retrain = pd.concat([data_first_retrain, data_first_retrain_current], axis=0)
                        last_start_time = period_end_time

                    data_first_retrain_current = self.aggregate_data_for_historic_averages_model(
                        agg_minutes=agg_minutes,
                        service_calls=[sc],
                        start_time=last_start_time,
                        end_time=max_request_timestamp)
                    data_first_retrain = pd.concat([data_first_retrain, data_first_retrain_current], axis=0)

            for sc in sc_regular:
                sc = sc[self._config.service_call_fields]
                n_ids_to_exclude = self.get_request_id_count_from_incidents(
                    incident_status=["incident"],
                    relevant_anomalous_metrics=relevant_anomalous_metrics,
                    max_incident_creation_timestamp=max_incident_creation_timestamp,
                    min_incident_creation_timestamp=min_incident_creation_timestamp, service_calls=[sc],
                    aggregation_timeunits=aggregation_timeunits)

                if n_ids_to_exclude < 1000000:
                    # exclude requests that are part of a "true" incident
                    ids_to_exclude = self.get_request_ids_from_incidents(
                        incident_status=["incident"],
                        relevant_anomalous_metrics=relevant_anomalous_metrics,
                        max_incident_creation_timestamp=max_incident_creation_timestamp,
                        min_incident_creation_timestamp=min_incident_creation_timestamp, service_calls=[sc],
                        aggregation_timeunits=aggregation_timeunits)

                    data_regular_current = self.aggregate_data_for_historic_averages_model(
                        agg_minutes=agg_minutes,
                        service_calls=[sc],
                        start_time=last_fit_timestamp,
                        end_time=max_request_timestamp,
                        ids_to_exclude=ids_to_exclude)
                    data_regular = pd.concat([data_regular, data_regular_current], axis=0)

                else:  # iterate by every incident for this service call
                    incidents_current = self.get_incidents(incident_status=["incident"],
                                                           relevant_anomalous_metrics=relevant_anomalous_metrics,
                                                           max_incident_creation_timestamp=max_incident_creation_timestamp,
                                                           min_incident_creation_timestamp=min_incident_creation_timestamp,
                                                           service_calls=[sc],
                                                           aggregation_timeunits=aggregation_timeunits)

                    last_start_time = last_fit_timestamp
                    for idd, period_start_time, period_end_time in incidents_current:
                        data_regular_current = self.aggregate_data_for_historic_averages_model(
                            agg_minutes=agg_minutes,
                            service_calls=[sc],
                            start_time=last_start_time,
                            end_time=period_start_time)
                        data_regular = pd.concat([data_regular, data_regular_current], axis=0)
                        last_start_time = period_end_time

                    data_regular_current = self.aggregate_data_for_historic_averages_model(
                        agg_minutes=agg_minutes,
                        service_calls=[sc],
                        start_time=last_start_time,
                        end_time=max_request_timestamp)
                    data_regular = pd.concat([data_regular, data_regular_current], axis=0)

        return data_regular, data_first_train, data_first_retrain

    def get_data_for_transform_stages(self, agg_minutes, last_transform_timestamp, current_transform_timestamp,
                                      sc_regular, sc_first_incidents):
        
        data_regular = pd.DataFrame()
        data_first_incidents = pd.DataFrame()
        
        # retrieve all data that have appeared after the last transform time
        data = self.aggregate_data_for_historic_averages_model(agg_minutes=agg_minutes,
                                                               start_time=last_transform_timestamp,
                                                               end_time=current_transform_timestamp)
        
        if len(data) > 0:
            # exclude service calls that are not past the training period
            data_regular = data.merge(sc_regular[self._config.service_call_fields])
        
        if len(sc_first_incidents) > 100:
            # for first-time incdent reporting, retrieve all data for these service calls
            data_first_incidents = self.aggregate_data_for_historic_averages_model(agg_minutes=agg_minutes,
                                                                                   end_time=current_transform_timestamp)
            if len(data_first_incidents) > 0:
                data_first_incidents = data_first_incidents.merge(sc_first_incidents[self._config.service_call_fields])
                
        elif len(sc_first_incidents) > 0:
                data_first_incidents = self.aggregate_data_for_historic_averages_model(
                    agg_minutes=agg_minutes,
                    end_time=current_transform_timestamp,
                    service_calls=sc_first_incidents[self._config.service_call_fields])
        
        return pd.concat([data_regular, data_first_incidents])
    
    def _get_incident_collection(self):
        db_client = MongoClient(self._db_config.MONGODB_URI)
        db = db_client[self._db_config.MONGODB_AD]
        return db.incident
    
    def _get_incident_model_collection(self):
        db_client = MongoClient(self._db_config.MONGODB_URI)
        db = db_client[self._db_config.MONGODB_AD]
        return db.incident_model
    
    def _get_incident_timestamp_collection(self):
        db_client = MongoClient(self._db_config.MONGODB_URI)
        db = db_client[self._db_config.MONGODB_AD]
        return db.incident_timestamps
    
    def _get_service_call_first_timestamps_collection(self):
        db_client = MongoClient(self._db_config.MONGODB_URI)
        db = db_client[self._db_config.MONGODB_AD]
        return db.service_call_first_timestamps
    
    def _get_clean_data_collection(self):
        db_client = MongoClient(self._db_config.MONGODB_URI)
        db = db_client[self._db_config.MONGODB_QD]
        return db.clean_data
    
    def _get_clean_data_projection_dict(self):
        project_dict = {col: {"$ifNull": ["$client.%s" % col, "$producer.%s" % col]}
                        for col in self._config.relevant_cols_nested}
        for col, field1, field2 in self._config.relevant_cols_general_alternative:
            project_dict[col] = {"$ifNull": ["$%s" % field1, "$%s" % field2]}
        for col in self._config.relevant_cols_general:
            project_dict[col] = "$%s" % col
        return project_dict
    
    def _generate_dataframe(self, result):
        data = pd.DataFrame(result)
        if len(data) > 0:
            data = pd.concat([data, pd.DataFrame(list(data["_id"]))], axis=1)
            data = data.drop(["_id"], axis=1)
            data.loc[:, self._config.timestamp_field] = pd.to_datetime(data.loc[:, self._config.timestamp_field], unit='ms')

            for col in self._config.service_call_fields:
                data.loc[:, col] = data.loc[:, col].fillna("-")

        return data
