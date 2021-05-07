#!/usr/bin/python3
from setuptools import setup

requirements = [
    "pymongo==3.10.1",
    "requests==2.22.0",
    "tqdm==4.30.0",
    "pyyaml==5.3.1"
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


setup(name='xroad-metrics-collector',
      version='0.1',
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
      license='MIT License'
      )
