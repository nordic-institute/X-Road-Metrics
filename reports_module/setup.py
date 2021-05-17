#!/usr/bin/python3
from setuptools import setup, find_packages

requirements = [
    "Jinja2==2.10.1",
    "matplotlib==3.1.2",
    "pandas",
    "weasyprint==51",
    "Pillow",
    "pymongo==3.10.1",
    "pyyaml==5.3.1",
    "requests==2.22.0",
    "tinycss==0.4",
    "jsonschema==3.2.0"
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
    name='xroad-metrics-reports',
    version='0.1',
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
    license='MIT License'
)
