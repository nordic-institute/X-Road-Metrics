#!/usr/bin/python3
from setuptools import setup, find_packages

requirements = [
    "pymongo==3.10.1",
    "pyyaml==5.3.1",
    "psycopg2==2.8.6",
    "python-dateutil==2.8.1",
]

classifiers = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 3',
    'Topic :: Utilities',
]

setup(
    name='xroad-metrics-anonymizer',
    version='0.1',
    description='X-Road Operational Monitoring anonymizer Module',
    long_description='',
    author='NIIS',
    author_email='info@niis.org',
    packages=find_packages(),
    include_package_data=True,
    scripts=['bin/xroad-metrics-anonymizer'],
    install_requires=requirements,
    classifiers=classifiers,
    platforms='POSIX',
    license='MIT License'
)
