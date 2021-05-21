#!/usr/bin/python3
from setuptools import setup, find_packages

requirements = [
    "dill==0.3.1.1",
    "pymongo==3.10.1",
    "pyyaml==5.3.1",
    "numpy",
    "pandas",
    "scipy"
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
    name='xroad-metrics-analysis',
    description='X-Road Operational Monitoring Analysis Module',
    long_description='',
    author='NIIS',
    author_email='info@niis.org',
    packages=find_packages(exclude=("tests", "analyzer_ui")),
    package_dir={'opmon_analyzer': 'opmon_analyzer'},
    scripts=['bin/xroad-metrics-analyzer'],
    install_requires=requirements,
    classifiers=classifiers,
    platforms='POSIX',
    license='MIT License'
)
