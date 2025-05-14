# X-Road Metrics Docker Containers

This directory contains Dockerfiles and scripts for building the containers for each module in the X-Road Metrics project.

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

## Overriding `settings.yaml` Values

Each module expects a `settings.yaml` file for configuration. By default, the container will use the `settings.yaml` included in the module directory. To override these settings:

1. Create your custom `settings.yaml` file with the desired configuration values.
2. When running the container, mount your custom file to the appropriate path inside the container. For example:

```bash
docker run -v /path/to/your/settings.yaml:/app/settings.yaml xroad-metrics-collector-module
```

Replace `/path/to/your/settings.yaml` with the absolute path to your custom file.

## Overriding Settings with Environment Variables (Entrypoint Script)

Instead of directly overriding individual settings via environment variables, the containers use an entrypoint script (`docker-entrypoint.sh`) that can substitute values in `settings.yaml` based on environment variables at container startup.

To override a value, set an environment variable matching the setting you want to change, using uppercase and underscores for dots. For example, to override `xroad.security-server.host=ss1` in `settings.yaml`, set the environment variable `xroad.security-server.host`:

```bash
docker run -e xroad.security-server.host=ss1 xroad-metrics-collector-module
```

The entrypoint script will update the `settings.yaml` file inside the container before starting the application, replacing the corresponding value with the environment variable's value. This allows you to override any setting in `settings.yaml` without modifying the file directly.

For more details on the supported environment variable format and substitution logic, see the comments in `Docker/docker-entrypoint.sh` and the main project documentation.

## Notes
- The `prepare-containers.sh` script will build all modules in sequence.
- For more details on module-specific configuration, see the documentation in `docs/` and the main project `README.md`.
