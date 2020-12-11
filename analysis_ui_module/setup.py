#!/usr/bin/python3
from setuptools import setup, find_packages

requirements = [
    "dill==0.3.1.1",
    "django==1.11.11",
    "pymongo==3.10.1",
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
    name='opmon-analysis',
    version='0.1',
    description='X-Road Operational Monitoring Analysis Module',
    long_description='',
    author='NIIS',
    author_email='info@niis.org',
    packages=find_packages(exclude=("tests", "analyzer_ui")),
    package_dir={'opmon_analyzer': 'opmon_analyzer'},
    scripts=['bin/opmon-analyzer'],
    install_requires=requirements,
    classifiers=classifiers,
    platforms='POSIX',
    license='MIT License'
)
