#!/usr/bin/python3
from setuptools import setup, find_packages

requirements = [
    "dill==0.3.1.1",
    "django==2.2.12",
    "pymongo==3.10.1",
    "pyyaml==5.3.1",
    "numpy"
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
    name='xroad-metrics-analysis-ui',
    description='X-Road Operational Monitoring Analysis UI Module',
    long_description='',
    author='NIIS',
    author_email='info@niis.org',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=classifiers,
    platforms='POSIX',
    license='MIT License'
)
