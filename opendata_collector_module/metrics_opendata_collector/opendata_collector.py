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

import datetime
from operator import itemgetter
from typing import Any, Dict, List, Tuple, Optional

import requests

from metrics_opendata_collector.constants import DT_FORMAT_WO_TZ
from metrics_opendata_collector.logger_manager import LoggerManager
from metrics_opendata_collector.mongodb_manager import MongoDbManager
from metrics_opendata_collector.opendata_api_client import (
    InputValidationError, OpenDataAPIClient)
from metrics_opendata_collector.settings import MetricsSettingsManager

from . import __version__


def collect_opendata(source_id: str, settings_manager: MetricsSettingsManager) -> None:
    """
    Collects and inserts OpenData from a given source into a MongoDB database.
    Uses an OpenDataAPIClient to fetch data, with optional query parameters based on the state of the last inserted entry.
    Logs relevant information using a LoggerManager.

    Args:
        source_id (str): ID of the OpenData source to collect from.
        settings_manager (MetricsSettingsManager): Instance of MetricsSettingsManager containing settings for fetching data.
    Returns:
        None. Inserts data into MongoDB."""  # noqa
    settings = settings_manager.settings
    source_settings = settings_manager.get_opendata_source_settings(source_id)

    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)
    mongo_manager = MongoDbManager(settings, source_id)
    client = OpenDataAPIClient(source_id, settings_manager)

    state = mongo_manager.get_last_inserted_entry()
    params_overrides = {}
    if state:
        params_overrides = _get_params_overrides(state)
    data = _get_opendata(client, logger_m, source_settings,
                         source_id, params_overrides)
    if not data:
        return
    total_inserted = 0
    if data.get('data'):
        total_query_count, inserted_documents = (
            _process_data(mongo_manager, logger_m, data, source_id)
        )
        total_inserted += len(inserted_documents)
        if total_query_count > len(inserted_documents):
            limit = source_settings['limit']
            offset = limit
            while total_inserted < total_query_count:
                params_overrides['offset'] = offset
                data = _get_opendata(client, logger_m, source_settings, source_id, params_overrides)
                if not data:
                    break
                total_query_count, inserted_documents = (
                    _process_data(mongo_manager, logger_m, data, source_id)
                )
                total_inserted += len(inserted_documents)
                offset += limit

    logger_m.log_info(
        'get_opendata',
        f'{source_id}: total inserted {total_inserted} opendata documents into MongoDB'
    )


def _process_data(mongo_manager: MongoDbManager, logger_m: LoggerManager,
                  data: dict, source_id: str) -> Tuple[int, List[dict]]:
    """
        Processes OpenData API response and saves the data to MongoDB.
        Args:
            mongo_manager (MongoDbManager): an instance of the MongoDbManager class for managing the MongoDB database
            logger_m (LoggerManager): an instance of the LoggerManager class for logging
            data (dict): a dictionary containing data returned by the OpenData API
            source_id (str): a string representing the ID of the OpenData source being processed
        Returns:
            total_query_count (int): an integer representing the total number of rows returned by the OpenData API
            documents (List[dict]): a list of dictionaries representing the processed OpenData documents to be inserted into the MongoDB database."""  # noqa

    rows = data['data']
    columns = data['columns']
    row_range = data['row_range']
    total_query_count = data['total_query_count']
    logger_m.log_info(
        'get_opendata',
        f'{source_id}: received {len(rows)} rows from total {total_query_count} within range {row_range}'
    )
    documents = _prepare_documents(rows, columns)
    _insert_documents(mongo_manager, documents)
    return total_query_count, documents


def _get_opendata(client: OpenDataAPIClient, logger_m: LoggerManager,
                  source_settings: dict, source_id: str,
                  params_overrides: Optional[dict] = None) -> Optional[dict]:
    """
    Fetches data from the OpenData API and logs the process.

    Args:
        client (OpenDataAPIClient): The OpenData API client.
        logger_m (LoggerManager): The logger manager.
        source_settings (dict): The source settings.
        source_id (str): The source ID.
        params_overrides (Optional[dict], optional): The optional parameter overrides. Defaults to None.

    Returns:
        Optional[dict]: The fetched data dictionary, or None if there was an error.
    """
    try:
        params_for_logging = client.get_query_params(params_overrides)
    except InputValidationError as err:
        logger_m.log_error('params_preparation_failed', str(err))
        return None
    logger_m.log_info(
        'get_opendata',
        (
            f'{source_id}: fetching opendata '
            f'from_dt: {params_for_logging["from_dt"]}, '
            f'from_row_id: {params_for_logging.get("from_row_id")} '
            f'until_dt: {params_for_logging.get("until_dt")}'
        )
    )
    try:
        data = client.do_request(params_overrides)
    except InputValidationError as err:
        logger_m.log_error('params_preparation_failed', str(err))
        return None
    except requests.exceptions.ConnectionError:
        logger_m.log_error(
            'get_opendata_connection_failed',
            f'Connection to {source_settings["url"]} failed'
        )
        return None
    except requests.exceptions.HTTPError as http_error:
        logger_m.log_error('get_opendata_main_failed', str(http_error))
        return None
    return data


def _get_params_overrides(state: dict) -> dict:
    """
    Return a dictionary of query parameter overrides for the OpenDataAPI client.

    Args:
        state (dict): A dictionary containing state information.
    Returns:
        dict: A dictionary containing query parameter overrides for the OpenDataAPI client.
    """
    params_overrides = {}
    if state:
        params_overrides['from_dt'] = _ts_to_dt_string(
            state['last_inserted_requestints'] / 1000,
            DT_FORMAT_WO_TZ
        )
        params_overrides['from_row_id'] = state['last_inserted_row_id']
    return params_overrides


def _ts_to_dt_string(ts: int, dt_format) -> str:
    """
    Converts a Unix timestamp to a datetime string in the specified format.
        Args:
            ts (int): Unix timestamp.
            dt_format (str): Desired datetime string format.
        Returns:
            str: Datetime string in the specified format.
    """
    dt_object = datetime.datetime.fromtimestamp(ts)
    return dt_object.strftime(dt_format)


def _insert_documents(mongo_manager: MongoDbManager, documents: List[dict]) -> None:
    """
    Insert documents into MongoDB and update the last inserted entry.
        Args:
            mongo_manager (MongoDbManager): Instance of MongoDB Manager.
            documents (List[dict]): List of documents to insert.
        Returns:
            None
    """
    mongo_manager.insert_documents(documents)
    docs_sorted = sorted(documents, key=itemgetter('requestInTs', 'id'), reverse=True)
    mongo_manager.set_last_inserted_entry(docs_sorted[0])


def _prepare_documents(rows: List[Tuple], columns: List[str]) -> List[dict]:
    """
    Prepare documents from rows and columns.
        Args:
            rows (List[Tuple]): A list of tuples containing data.
            columns (List[str]): A list of column names.

        Returns:
            List[dict]: A list of dictionaries containing the prepared documents.
    """
    documents = []
    for data in rows:
        normalized = [None if entry == 'None' else entry for entry in data]
        doc: Dict[str, Any] = dict(zip(columns, normalized))
        doc['requestInTs'] = int(doc['requestInTs'])
        if doc.get('totalDuration'):
            doc['totalDuration'] = int(doc.get('totalDuration') or 0)
        if doc.get('producerDurationProducerView'):
            doc['producerDurationProducerView'] = int(doc.get('producerDurationProducerView') or 0)
        documents.append(doc)
    return documents
