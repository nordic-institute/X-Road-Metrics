#!/usr/bin/python3
from setuptools import setup

setup(name='opmon-collector',
      version='0.1',
      description='X-Road Operational Monitoring Collector Module',
      long_description='',
      author='NIIS',
      author_email='info@niis.org',
      packages=['opmon_collector'],
      package_dir={'opmon_collector': 'opmon_collector'},
      scripts=['bin/opmon-collector'],
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: System Administrators',
                   'License :: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3',
                   'Topic :: Utilities',
                   ],
      platforms='POSIX',
      license='MIT License'
      )
