import argparse
import time
from multiprocessing import Manager, Process

from opmon_corrector.corrector_batch import CorrectorBatch
from opmon_corrector.logger_manager import LoggerManager
from opmon_corrector.settings_parser import OpmonSettingsManager


def main():
    args = parse_args()
    settings = OpmonSettingsManager(args.profile).settings
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'])
    # Runs Corrector in infinite Loop
    while True:
        try:
            process_dict = run_batch(settings, logger_m)
            handle_results(process_dict, settings, logger_m)
        except Exception as e:
            logger_m.log_error('corrector_main', f'Internal error: {repr(e)}')
            logger_m.log_heartbeat("error", "FAILED")
            # If here, it is not possible to restart the processing batch. Raise exception again
            raise e


def run_batch(settings, logger_m: LoggerManager):
    corrector_version = logger_m.__version__
    c_batch = CorrectorBatch(settings, logger_m)
    manager = Manager()
    process_dict = manager.dict()
    process_dict['doc_len'] = -1

    print('Corrector Service [{0}] - Batch timestamp: {1}'.format(corrector_version, int(time.time())))
    p = Process(target=c_batch.run, args=(process_dict,))
    p.start()
    p.join()

    return process_dict


def handle_results(process_dict, settings, logger_m):
    # Wait 5 sec between successful batches to allow external kill
    wait_time = 5

    if process_dict['doc_len'] == -1:
        wait_time = settings["corrector"]["wait-on-error"]
        logger_m.log_error('corrector_main', 'Corrector batch finished with error code.')
        logger_m.log_heartbeat("error", "FAILED")

    elif process_dict['doc_len'] < settings["corrector"]["documents-min"]:
        wait_time = settings["corrector"]["wait-on-done"]
        doc_min = settings["corrector"]["documents-min"]
        message = f'Processed {process_dict["doc_len"]} docs, which is under the minimum batch size {doc_min}.'
        logger_m.log_info('corrector_main', message)

    logger_m.log_info('corrector_main', f'Next batch starting in {wait_time} seconds.')
    time.sleep(wait_time)
    logger_m.log_info('corrector_main', 'Done waiting. Next batch starting now.')


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--profile",
        metavar="PROFILE",
        default=None,
        help="""
            Optional settings file profile.
            For example with '--profile PROD' settings_PROD.yaml will be used as settings file.
            If no profile is defined, settings.yaml will be used by default.
            Settings file is searched from current working directory and /etc/opmon/corrector/
        """
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
