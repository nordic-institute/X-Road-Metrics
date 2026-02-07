# X-Road Metrics E2E Tests <!-- omit in toc -->

## Table of Contents <!-- omit in toc -->

- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Configuration](#configuration)
- [Directory Structure](#directory-structure)
- [Debugging](#debugging)
- [Developer Iteration Workflow](#developer-iteration-workflow)
  - [Initial Setup (once)](#initial-setup-once)
  - [Iteration Loop](#iteration-loop)
  - [Module Run Commands](#module-run-commands)
  - [Cleanup](#cleanup)


End-to-end test automation for X-Road Metrics `.deb` packages. Validates the full data pipeline (collector, corrector, anonymizer, opendata) across Ubuntu distros and database versions.

- **LXD** provides the Ubuntu environment for package installation
- **Docker** runs databases (MongoDB, PostgreSQL) and WireMock mock services

## Prerequisites

- **LXD** (`sudo snap install lxd && lxd init`)
- **Docker** + **Docker Compose**

## Usage

```bash
cd e2e_tests

# Build .deb packages for jammy and noble
./run.sh build

# Build specific modules only
./run.sh build collector_module corrector_module

# Fresh install on noble with latest DB versions
./run.sh test-noble-latest-dbs

# Same, but against a real X-Road environment
./run.sh test-noble-latest-dbs --real-xroad

# Upgrade test: old packages + old DBs -> upgrade packages -> verify
./run.sh test-upgrade

# Keep containers after test (for manual verification)
./run.sh test-noble-latest-dbs --always-keep

# Cleanup containers
./run.sh clean
```

> [!NOTE]
>
> - Run `./run.sh` without arguments to see all available commands.
> - Packages must be built before running test scenarios (`./run.sh build`).
> - By default, containers are removed on success and kept on failure for debugging. Use `--always-keep` or `--always-clean` to override.

### Using Real X-Road Servers

To test against real X-Road servers running in Docker containers on the same host, the script automatically detects their IPs (LXD can reach Docker's bridge network directly).

The script looks for containers named `cs` (central server) and `ss0` (security server). Just run:

```bash
./run.sh test-noble-latest-dbs --real-xroad
```

## Configuration

Review [config/env.sh](./config/env.sh) before running tests. It defines database versions, credentials, ports, and the artifactory URL for old packages. All scripts source this file.

## Directory Structure

```text
X-Road-Metrics/
 ├── output/                                  # Build artifacts at repo root (created at runtime)
 │    └── artifacts/{jammy,noble}/            # .deb packages
 └── e2e_tests/
      ├── run.sh                              # Command dispatcher
      ├── config/env.sh                       # Environment config
      ├── docker/
      │   ├── docker-compose.dbs.yml          # MongoDB + PostgreSQL
      │   ├── docker-compose.mock-xroad.yml   # WireMock
      │   └── mock-xroad/                     # Mock responses
      └── scripts/
          ├── scenarios/                      # Test scenarios
          └── helpers/                        # Shared helper scripts
```

## Debugging

Containers are kept on failure for debugging. On success they are cleaned up automatically.

```bash
lxc exec xroad-metrics-e2e-noble -- bash       # Access LXD container
./run.sh clean                                 # Manual cleanup when done
```

## Developer Iteration Workflow

When iterating on a single module, you don't need to run the full pipeline every time.

### Initial Setup (once)

Run the full test with `--always-keep` to create a working environment with data:

```bash
./run.sh test-noble-latest-dbs --always-keep
```

### Iteration Loop

- Make changes to your module. e.g., corrector_module
- Build just that module:

  ```bash
  ./run.sh build corrector_module
  ```

- Deploy to the running container:

  ```bash
  lxc file push output/artifacts/noble/xroad-metrics-corrector_*.deb xroad-metrics-e2e-noble/tmp/
  lxc exec xroad-metrics-e2e-noble -- apt install -y /tmp/xroad-metrics-corrector_*.deb
  ```

- Re-run your module (see commands below)

### Module Run Commands

Connect to the container and run commands as the `xroad-metrics` user:

```bash
lxc exec xroad-metrics-e2e-noble -- bash
cd /tmp
sudo -u xroad-metrics xroad-metrics-correctord
```

### Cleanup

When done iterating, clean up all containers:

```bash
./run.sh clean
```
