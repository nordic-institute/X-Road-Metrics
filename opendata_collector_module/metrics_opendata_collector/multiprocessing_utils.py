#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#
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
