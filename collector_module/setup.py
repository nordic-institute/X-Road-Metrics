#!/usr/bin/python3

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

from setuptools import setup

requirements = [
    'setuptools==67.4.0',
    'pymongo==4.6.3',
    'requests==2.32.3',
    'tqdm==4.66.4',
    'pyyaml==6.0.1',
    'urllib3==1.26.18',
]

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 3',
    'Topic :: Utilities',
]


setup(name='xroad-metrics-collector',
      description='X-Road Metrics Collector Module',
      long_description='',
      author='NIIS',
      author_email='info@niis.org',
      packages=['opmon_collector', 'opmon_mongodb_maintenance'],
      package_dir={'opmon_collector': 'opmon_collector', 'opmon_mongodb_maintenance': 'opmon_mongodb_maintenance'},
      scripts=['bin/xroad-metrics-collector', 'bin/xroad-metrics-init-mongo'],
      install_requires=requirements,
      classifiers=classifiers,
      platforms='POSIX',
      license='MIT'
      )
