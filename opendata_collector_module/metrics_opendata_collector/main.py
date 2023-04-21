#!/usr/bin/env python3

#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal # noqa
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
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  # noqa
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import argparse

from metrics_opendata_collector.multiprocessing_utils import (
    run_collect_opendata_in_parallel
)
from metrics_opendata_collector.settings import MetricsSettingsManager


def main():
    args = parse_args()
    settings_manager = MetricsSettingsManager(args.profile)

    settings = settings_manager.settings
    run_collect_opendata_in_parallel(
        args.source_id,
        settings_manager,
        settings['opendata-collector']['thread-count']
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('source_id',
                        metavar='SOURCE_ID',
                        help='X-Road Metrics instance to fetch OpenData from. Taken from sources settings file')  # noqa

    parser.add_argument('--profile',
                        metavar='PROFILE',
                        default=None,
                        help="""
                            Optional settings file profile.
                            For example with '--profile PROD' settings_PROD.yaml will be used as settings file.
                            If no profile is defined, settings.yaml will be used by default.
                            Settings file is searched from current working directory and /etc/xroad-metrics/opendata-collector/
                        """.strip()  # noqa
                        )
    args = parser.parse_args()

    return args
