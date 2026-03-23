# X-Road Metrics Docker Containers <!-- omit in toc -->

## Table of Contents <!-- omit in toc -->

- [Introduction](#introduction)
- [Hardware requirements](#hardware-requirements)
- [Building All Containers](#building-all-containers)
- [Overriding `settings.yaml` Values](#overriding-settingsyaml-values)
- [Overriding Settings with Environment Variables (Entrypoint Script)](#overriding-settings-with-environment-variables-entrypoint-script)
- [Container Logging](#container-logging)
- [Running the environment](#running-the-environment)
- [Cleanup](#cleanup)

## Introduction

This directory contains Dockerfiles and scripts for building the containers for each module in the X-Road Metrics project. And
running them with Docker Compose.

The Docker Compose setup expects that the [xrd-dev-stack](https://github.com/nordic-institute/X-Road/tree/develop/Docker/xrd-dev-stack)
has been set up and configured with the monitoring client (note that the subsystem must be created and configured manually):

```xml
<tns:conf xmlns:id="http://x-road.eu/xsd/identifiers"
          xmlns:tns="http://x-road.eu/xsd/xroad.xsd"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://x-road.eu/xsd/xroad.xsd">
    <monitoringClient>
        <monitoringClientId id:objectType="SUBSYSTEM">
            <id:xRoadInstance>DEV</id:xRoadInstance>
            <id:memberClass>COM</id:memberClass>
            <id:memberCode>1234</id:memberCode>
            <id:subsystemCode>metrics</id:subsystemCode>
        </monitoringClientId>
    </monitoringClient>
</tns:conf>
```

The subsystem should have `HTTP` selected as the connection method.

## Hardware requirements

This Docker setup is only intended for limited local testing. Most modules run only when explicitly ran. Only the following containers run
continuously, with the `corrector` running in batches:

- Corrector
- Opendata
- MongoDB
- PostgreSQL
- Mongo Express
- Adminer

These all have a relatively small footprint unless pushed - the more data you want to test with, the more database and corrector resource
usage you will see. The setup itself can be ran with **1GB** of memory, potentially less if datasets are really small.

## Building All Containers

To build all module containers, run the build script from the project root:

```bash
bash Docker/prepare-containers.sh
```

The script can also be run from any directory using an absolute path.

This will build Docker images for:

- xroad-metrics-collector-module
- xroad-metrics-corrector-module
- xroad-metrics-anonymizer-module
- xroad-metrics-opendata-module
- xroad-metrics-opendata-collector-module
- xroad-metrics-reports-module
- xroad-metrics-networking-module

To build specific modules, you can specify one or more module names:

```bash
bash Docker/prepare-containers.sh collector_module
bash Docker/prepare-containers.sh collector_module corrector_module
```

> [!NOTE]
>
> - The `prepare-containers.sh` script will build all modules in sequence.
> - For more details on module-specific configuration, see the documentation in `docs/` and the main project `README.md`.

## Overriding `settings.yaml` Values

Each module expects a `settings.yaml` file for configuration. By default, the container will use the `settings.yaml` included in the
module directory. To override these settings:

1. Create your custom `settings.yaml` file with the desired configuration values.
2. When running the container, mount your custom file to the appropriate path inside the container. For example:

```bash
docker run -v /path/to/your/settings.yaml:/app/settings.yaml xroad-metrics-collector-module
```

Replace `/path/to/your/settings.yaml` with the absolute path to your custom file.

## Overriding Settings with Environment Variables (Entrypoint Script)

Instead of directly overriding all settings via replacing the settings file, the containers can override entries in the
`settings.yaml` file with functionality in the entrypoint script (`docker-entrypoint.sh`) that can substitute values based on
environment variables at container startup.

To override a value, set an environment variable matching the setting you want to change, but prefix it with `setting_`. The prefix
will be stripped when mapping to the YAML key. For example, to override `xroad.security-server.host=ss1` in `settings.yaml`, set the
environment variable `setting_xroad.security-server.host`:

```bash
docker run -e setting_xroad.security-server.host=ss1 xroad-metrics-collector-module
```

The entrypoint script will update the `settings.yaml` file inside the container before starting the application, replacing the
corresponding value with the environment variable's value. This allows you to override any setting in `settings.yaml` without
modifying the file directly. Note that this will also do substitutions in your `settings.yaml` if you have mounted it.

For more details on the supported environment variable format and substitution logic, see the comments in
`Docker/docker-entrypoint.sh` and the main project documentation.

## Container Logging

By default, the [entrypoint script](./docker-entrypoint.sh) redirects module log files to stdout by creating symlinks. This allows viewing logs
via `docker logs` or `docker compose logs` instead of accessing files inside the container.

The following logs are redirected:

- Main module log: `log_<logger-name>_<instance>.json`
- Networking module's data preparation log: `prepare_data_log.json`

> [!NOTE]
> In case of Networking module, Shiny server will produce a warning about log file is created as a symlink. 
> This warning can be ignored.

## Running the environment

From the `Docker` directory, follow these steps:

- **Databases**

```bash
docker compose up -d mongodb postgresql
```

- **_(Optional)_ Run web UIs for databases**

```bash
docker compose up -d mongo-express adminer
```

UIs are accessible via http://localhost:8081 and http://localhost:8082 respectively.
For passwords, review the [docker-compose.yaml](./docker-compose.yaml) file.

- **Collector**

```bash
docker compose run --rm collector_module update
```

and then 

```bash
docker compose run --rm collector_module collect
```

- **Corrector**

```bash
docker compose up -d corrector_module
```

- **Reports** for data up to today's date:

```bash
docker compose run --rm reports_module --end-date $(date +%Y-%m-%d) report
```

- **Anonymizer**

```bash
docker compose run --rm anonymizer_module
```

- **Opendata**

```bash
docker compose up -d opendata_module
```

UI is accessible on port `8000` via http://localhost:8000.

- **Networking**

```bash
docker compose up -d networking_module
```

UI is accessible on port `8001` via http://localhost:8001.

- **Opendata Collector**, if needed:

```bash
docker compose run --rm opendata_collector_module
```

## Cleanup

To remove all X-Road Metrics containers, volumes, and networks created by Docker Compose:

```bash
docker compose down -v
```

To remove all X-Road Metrics images:

```bash
docker image rm $(docker images 'xroad-metrics-*' -q)
```
