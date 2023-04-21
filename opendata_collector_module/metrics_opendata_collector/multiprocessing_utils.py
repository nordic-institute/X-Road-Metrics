from multiprocessing import Process

from metrics_opendata_collector.opendata_collector import collect_opendata


def run_collect_opendata_in_parallel(source_id: str, settings_manager, thread_count: int):
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
