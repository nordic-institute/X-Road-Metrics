from multiprocessing import Process

from metrics_opendata_collector.opendata_collector import collect_opendata


def run_collect_opendata_in_parallel(source_id: str, settings_manager, thread_count: int) -> None:
    """
    Runs the `collect_opendata` function in parallel using multiple processes.

    Args:
        source_id (str): A unique identifier for the OpenData instance.
        settings_manager: An object containing settings for the data collection process.
        thread_count (int): The number of threads to use for parallel execution.

    Returns:
        None
    """
    pool = []
    for i in range(thread_count):
        p = Process(
            target=collect_opendata,
            args=(
                source_id,
                settings_manager
            )
        )
        pool.append(p)
    for p in pool:
        p.start()
        p.join()
