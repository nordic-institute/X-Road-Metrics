#!/usr/bin/python3
from setuptools import setup

requirements = [
    "pymongo==3.10.1",
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

setup(
    name='opmon-corrector',
    version='0.1',
    description='X-Road Operational Monitoring Corrector Module',
    long_description='',
    author='NIIS',
    author_email='info@niis.org',
    packages=['opmon_corrector'],
    package_dir={'opmon_corrector': 'opmon_corrector'},
    scripts=['bin/opmon-correctord'],
    install_requires=requirements,
    classifiers=classifiers,
    platforms='POSIX',
    license='MIT License'
)
