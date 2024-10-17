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

# The following dependencies has newer versions, but require Python 3.9 or higher
#   matplotlib, pandas, weasyprint, numpy, contourpy

requirements = [
    'markupsafe==2.1.5',
    'Jinja2==3.1.4',
    'matplotlib==3.9.2',
    'pandas==2.2.3',
    'weasyprint==61.2',
    'Pillow==10.4.0',
    'pymongo==4.10.1',
    'pyyaml==6.0.2',
    'requests==2.32.3',
    'tinycss==0.4',
    'jsonschema==4.23.0',
    'numpy==1.24.4',
    'contourpy==1.3.0',
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
    name='xroad-metrics-reports',
    description='X-Road Operational Monitoring Reports Module',
    long_description='',
    author='NIIS',
    author_email='info@niis.org',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    scripts=['bin/xroad-metrics-reports'],
    classifiers=classifiers,
    platforms='POSIX',
    license='MIT'
)
