# Developer Guide <!-- omit in toc -->

## Table of Contents <!-- omit in toc -->

- [Introduction](#introduction)
- [Setup Development Environment](#setup-development-environment)
  - [Generic Steps](#generic-steps)
    - [Install make](#install-make)
    - [Install pyenv](#install-pyenv)
    - [Install Python](#install-python)
    - [Install setuptools](#install-setuptools)
    - [Install tox](#install-tox)
  - [Module Specific Steps](#module-specific-steps)
    - [Create a virtual environment](#create-a-virtual-environment)
    - [Activate the virtual environment](#activate-the-virtual-environment)
- [Development Workflow](#development-workflow)
  - [Run lint checks, type checking, and tests](#run-lint-checks-type-checking-and-tests)
  - [Run lint checks only](#run-lint-checks-only)
  - [Run type checking only](#run-type-checking-only)
  - [Run tests only](#run-tests-only)
- [Creating a pull request](#creating-a-pull-request)
  - [Prerequisites](#prerequisites)
  - [Branch naming, PRs, and commit messages](#branch-naming-prs-and-commit-messages)
- [Building a docker image](#building-a-docker-image)
- [Packaging modules](#packaging-modules)
- [Useful commands](#useful-commands)
  - [Display list of installed virtual environments](#display-list-of-installed-virtual-environments)
  - [Deactivate the virtual environment](#deactivate-the-virtual-environment)
  - [Remove the virtual environment](#remove-the-virtual-environment)
  - [Display the list of installed Python versions](#display-the-list-of-installed-python-versions)
  - [Remove the Python version](#remove-the-python-version)

## Introduction

This document provides a guide for developers to set up their development environment and contribute to the project.  
Steps consists of generic steps that are required only once, 
and module-specific steps that are required for each module.
The document also provides information on how to contribute to the project.

## Setup Development Environment

### Generic Steps

The following steps are required only once when setting up the development environment.

#### Install make

```bash
sudo apt install make
```

#### Install pyenv

> [!NOTE]
> For up-to-date installation instructions, please refer to [official website](https://github.com/pyenv/pyenv-installer)

```bash
curl https://pyenv.run | bash
```

#### Install Python

To get a list of latest Python versions available:
```bash
pyenv install --list | grep 3.10
```

Currently, the latest version is `3.10.19`. To install it:

```bash
pyenv install 3.10.19
```

Set the global Python version to `3.10.19`:

```bash
pyenv global 3.10.19
```

#### Install setuptools

```bash
pip install setuptools
```

#### Install tox

> [!NOTE]
> If tox is installed globally, it will be available for all virtual environments.  
> If it's not installed globally, you will need to install it for each virtual environment.

```bash
pip install tox
```

### Module Specific Steps

The following steps are required for each module when setting up the development environment.

#### Create a virtual environment

> [!NOTE]
> Replace `collector` with the module's name

```bash
pyenv virtualenv collector
```

#### Activate the virtual environment

> [!NOTE]
> Replace `collector` with the module's name

```bash
pyenv activate collector
```

## Development Workflow

After following the setup steps, you can start developing the module.
The following commands are available for each module.

### Run lint checks, type checking, and tests

The following command will run lint checks, type checking, and tests:

```bash
tox
```

### Run lint checks only

```bash
tox -e lint
```

### Run type checking only

```bash
tox -e type
```

### Run tests only

```bash
tox -e py310
```

## Creating a pull request

### Prerequisites

> [!IMPORTANT]
> When opening a pull request, please provide a signed Contributor Licence Agreement (CLA). More information can be found
> [here](https://github.com/nordic-institute/X-Road/blob/develop/CONTRIBUTING.md#legal-notice).

For each module, run `tox` to make sure that the code is linted, typed, and tested.

```bash
tox
```

For each module, make sure that the license headers are up to date using this command:

```bash
make license
```

### Branch naming, PRs, and commit messages

Please follow the style guide for branch names, PRs, and commit messages 
as described in the [style guide](https://github.com/nordic-institute/X-Road/blob/develop/CONTRIBUTING.md#styleguides).

## Building a docker image

To build a docker image or run module(s) in docker, please refer to [Docker README](../../Docker/README.md).

## Packaging modules

In order to create `.deb` packages for a module, each module is built inside a controlled Docker environment that reproduces the target Ubuntu release. The Dockerfile installs all required build tools and dependencies, compiles the module, and uses Debian's packaging utilities such as dpkg-buildpackage to generate the .deb file. This ensures consistent, reproducible builds that match the expected distribution environment.

Use the `build-packages.sh` script in the project root to build packages:

```shell
# Build all modules for all targets
./build-packages.sh

# Build a specific module for all targets
./build-packages.sh collector_module

# Build all modules for a specific target
./build-packages.sh -t noble

# Build specific modules for a specific target
./build-packages.sh -t noble collector_module corrector_module
```

Run `./build-packages.sh --help` for full usage information.

After building, you can check the created package for compliance with the Debian policy and for other common packaging errors using:

```shell
lintian output/<target>/*.deb
```

## Useful commands

### Display list of installed virtual environments

```bash
pyenv virtualenvs
```

An example output:  
_The `*` indicates which virtualenv is active._

```bash
  3.10.16/envs/collector (created from /home/xrduser/.pyenv/versions/3.10.16)
* collector (created from /home/xrduser/.pyenv/versions/3.10.16)
```

### Deactivate the virtual environment

```bash
pyenv deactivate
```

### Remove the virtual environment

```bash
pyenv virtualenv-delete collector
```

### Display the list of installed Python versions

```bash
pyenv versions
```

### Remove the Python version

```bash
pyenv uninstall 3.10.19
```
