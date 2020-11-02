import time
from multiprocessing import Pool

from opmon_collector.database_manager import DatabaseManager
from opmon_collector.logger_manager import LoggerManager
from opmon_collector.collector_worker import run_collector_thread


def prepare_thread_inputs(settings, server_list, server_m, logger_m):
    inputs = []

    for server in server_list:
        data = dict()
        data['settings'] = settings
        data['logger_manager'] = logger_m
        data['server_manager'] = server_m
        data['server_data'] = server
        inputs.append(data)

    return inputs


def process_thread_pool(settings, inputs):
    pool = Pool(processes=settings['collector']['thread-count'])
    results = pool.map(run_collector_thread, inputs)
    done = results.count(True)
    error = len(results) - done
    return done, error


def run_threaded_collector(logger_m, settings):
    server_m = DatabaseManager(settings['mongodb'], settings['xroad'], logger_m)

    logger_m.log_info('collector_start', f'Starting collector - Version {LoggerManager.__version__}')

    start_processing_time = time.time()
    server_list, timestamp = server_m.get_server_list_from_database()
    print(f'- Using server list updated at: {timestamp}')

    inputs = prepare_thread_inputs(settings, server_list, server_m, logger_m)
    done, error = process_thread_pool(settings, inputs)

    end_processing_time = time.time()
    total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
    logger_m.log_info('collector_end', f'Total collected: {done}, Total error: {error}, Total time: {total_time}')
    logger_m.log_heartbeat(f'Total collected: {done}, Total error: {error}, Total time: {total_time}', "SUCCEEDED")


def collector_main(settings):

    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'])

    try:
        run_threaded_collector(logger_m, settings)
    except Exception as e:
        logger_m.log_error('collector', '{0}'.format(repr(e)))
        logger_m.log_heartbeat("error", "FAILED")
        raise e
