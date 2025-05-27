# X-Road Metrics Docker Containers

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

## Harware requirements

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

To build all module containers, run the following script from the project root:

```bash
bash Docker/prepare-containers.sh
```

This will build Docker images for:
- xroad-metrics-collector-module
- xroad-metrics-corrector-module
- xroad-metrics-anonymizer-module
- xroad-metrics-opendata-module
- xroad-metrics-opendata-collector-module
- xroad-metrics-reports-module

To build just one module, you can run the command with:

```bash
bash Docker/prepare-containers.sh [module_name]
```

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

## Running the environment

The containers can be ran with `docker compose up -d` in the `Docker` directory. After this you can run specific commands such
as collecting by running it on the container, for example:

```bash
docker compose run --rm collector_module collect
```

There is a web based UI for both the MongoDB and PostgreSQL databases on ports `8081` and `8082` respectively. For passwords,
review the `docker-compose.yaml` file.

## Notes
- The `prepare-containers.sh` script will build all modules in sequence.
- For more details on module-specific configuration, see the documentation in `docs/` and the main project `README.md`.
