# Developer Guide

## Table of Contents

- [Developer Guide](#developer-guide)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Setup Development Environment](#setup-development-environment)
    - [Generic Steps](#generic-steps)
      - [Install make](#install-make)
      - [Install pyenv](#install-pyenv)
      - [Install Python](#install-python)
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
  - [Useful commands](#useful-commands)
    - [Display list of installed virtual environments](#display-list-of-installed-virtual-environments)
    - [Deactivate the virtual environment](#deactivate-the-virtual-environment)
    - [Remove the virtual environment:](#remove-the-virtual-environment)
    - [Display the list of installed Python versions:](#display-the-list-of-installed-python-versions)
    - [Remove the Python version:](#remove-the-python-version)

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
pyenv install --list | grep 3.8
```

Currently, the latest version is `3.8.20`. To install it:

```bash
pyenv install 3.8.20
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

```bash
pyenv virtualenv collector
```

_**Note:** replace `collector` with the module's name_

#### Activate the virtual environment

```bash
pyenv activate collector
```

_**Note:** replace `collector` with the module's name_

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
tox -e py38
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

Before building a docker image, clean up the project to reduce image size.  
_`tox` command caches a lot of files that might be over 500MB._

```bash
make clean
```

## Useful commands

### Display list of installed virtual environments

```bash
pyenv virtualenvs
```

An example output:  
_The `*` indicates which virtualenv is active._

```bash
  3.8.20/envs/collector (created from /home/xrduser/.pyenv/versions/3.8.20)
* collector (created from /home/xrduser/.pyenv/versions/3.8.20)
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
pyenv uninstall 3.8.20
```
