#!/usr/bin/python3
from setuptools import setup

requirements = [
    "pymongo>=3.4,<4",
    "requests>=2.24,<3",
    "numpy>=1.19,<2",
    "tqdm>=4.14<5",
    "pyaml>=20.4.0"
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


setup(name='opmon-collector',
      version='0.1',
      description='X-Road Operational Monitoring Collector Module',
      long_description='',
      author='NIIS',
      author_email='info@niis.org',
      packages=['opmon_collector', 'opmon_mongodb_maintenance'],
      package_dir={'opmon_collector': 'opmon_collector', 'opmon_mongodb_maintenance': 'opmon_mongodb_maintenance'},
      scripts=['bin/opmon-collector', 'bin/opmon-init-mongo'],
      install_requires=requirements,
      classifiers=classifiers,
      platforms='POSIX',
      license='MIT License'
      )
