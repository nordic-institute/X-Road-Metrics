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

from setuptools import setup, find_packages

requirements = [
    'setuptools==75.1.0',
    'dill==0.3.9',
    'django==5.1.1',
    'pymongo==4.9.1',
    'pyyaml==6.0.2',
    'psycopg2==2.9.9',
    'python-dateutil==2.9.0.post0',
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

setup(
    name='xroad-metrics-opendata',
    description='X-Road Metrics Opendata Module',
    long_description='',
    author='NIIS',
    author_email='info@niis.org',
    packages=find_packages(exclude=("*.tests", "tests",)),
    scripts=['bin/xroad-metrics-init-postgresql'],
    include_package_data=True,
    install_requires=requirements,
    classifiers=classifiers,
    platforms='POSIX',
    license='MIT'
)
