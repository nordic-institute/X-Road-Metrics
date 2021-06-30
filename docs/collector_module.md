
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Collector Module

## About

The **Collector module** is part of [X-Road Metrics](../README.md), which includes the following modules:
 - [Database module](../database_module.md)
 - [Collector module](../collector_module.md)
 - [Corrector module](../corrector_module.md) 
 - [Reports module](../reports_module.md) 
 - [Anonymizer module](../anonymizer_module.md)
 - [Opendata module](../opendata_module.md) 
 - [Networking/Visualizer module](../networking_module.md)

The **Collector module** is responsible to retrieve data from X-Road security servers and insert into the database module. The execution of the collector module is performed automatically via a **cron job** task.

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in one server, but also in separate servers. Opmon modules are controlled by unix user 'opmon' in group 'opmon'.

Overall system is also designed in a way, that allows to monitor data from different X-Road instances (e.g. in Estonia there are three instances: `ee-dev`, `ee-test` and `EE`.)

Overall system is also designed in a way, that can be used by X-Road Centre for all X-Road members as well as for Member own monitoring (includes possibilities to monitor also members data exchange partners).


## Networking

### Outgoing

- The collector module needs HTTP-access to the X-Road Central Server to get from global configuration list of members security servers.
- The collector module needs HTTP-access to an X-Road Security Server that acts as an Operational Monitoring Client to get the data is collected.
- The collector module needs access to the Database Module (see ==> [Database_Module](database_module.md) <==).

### Incoming

No incoming connection is needed in the collector module.

## Installation

This sections describes the necessary steps to install the **collector module** on a Ubuntu 20.04 Linux host. For a complete overview of different modules and machines, please refer to the ==> [System Architecture](system_architecture.md) <== documentation.


### Add X-Road Extensions Package Repository for Ubuntu
````bash
wget -qO - https://artifactory.niis.org/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository 'https://artifactory.niis.org/xroad-extensions-release-deb main'
````

The following information can be used to verify the key:
- key hash: 935CC5E7FA5397B171749F80D6E3973B
- key fingerprint: A01B FE41 B9D8 EAF4 872F A3F1 FB0D 532C 10F6 EC5B
- 3rd party key server: [SKS key servers](http://pool.sks-keyservers.net/pks/lookup?op=vindex&hash=on&fingerprint=on&search=0xFB0D532C10F6EC5B)


### Install Collector Package
To install xroad-metrics-collector and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install xroad-metrics-collector
```

The installation package automatically installs following items:
 * xroad-metrics-collector command to run the collector manually
 * Linux user named _xroad-metrics_ and group _xroad-metrics_
 * settings file _/etc/xroad-metrics/collector/settings.yaml_
 * cronjob in _/etc/cron.d/xroad-metrics-collector-cron_ to run collector automatically every three hours
 * log folders to _/var/log/xroad-metrics/collector/_

Only _xroad-metrics_ user can access the settings files and run xroad-metrics-collector command.

To use collector you need to fill in your X-Road and MongoDB configuration into the settings file.
Refer to section [Collector Configuration](#collector-configuration)


## Usage
### Collector Configuration

Before using the Collector module, make sure you have installed and configured the [Database_Module](database_module.md)
and created the MongoDB credentials.

To use collector you need to fill in your X-Road and MongoDB configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/xroad-metrics/collector/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* central- and security server hosts
* X-Road client used to collect the monitoring data
* username and password for the collector module MongoDB user

To run collector for multiple X-Road instances, a settings profile for each instance can be created. For example to have profiles DEV, TEST and PROD create three copies of `setting.yaml` 
file named `settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml`.
Then fill the profile specific settings to each file and use the --profile
flag when running xroad-metrics-collector. For example to run using the TEST profile:
```
xroad-metrics-collector --profile TEST collect
```

`xroad-metrics-collector` command searches the settings file first in current working direcrtory, then in
_/etc/xroad-metrics/collector/_

### Manual usage

All collector module actions can be executed by calling the `xroad-metrics-collector` command.
Command should be executed as user `xroad-metrics` so change to that user:
```bash
sudo su xroad-metrics
```

Some example commands:
```bash
xroad-metrics-collector list                       # Print available security servers to stdout.
xroad-metrics-collector update                     # Update security server list to MongoDB.
xroad-metrics-collector collect                    # Collect monitoring data from security server.
xroad-metrics-collector settings get mongodb.host  # Read a value from settings file and print to stdout
```

Above examples use the default settings file. To use another settings profile, you can use --profile flag:
```bash
xroad-metrics-collector --profile TEST update
xroad-metrics-collector --profile TEST collect
```

### Cron settings
Default installation includes a cronjob in _/etc/cron.d/xroad-metrics-collector-cron_ that runs collector every three hours. This job runs collector using default settings profile (_/etc/xroad-metrics/collector/settings.yaml_)

If you want to change the collector cronjob scheduling or settings profiles, edit the file e.g. with vi
```
vi /etc/cron.d/xroad-metrics-collector-cron
```
and make your changes. For example to run collector every six hours using settings profiles PROD and TEST:
```bash
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# m   h  dom mon dow  user       command
  15 */6  *   *   *   xroad-metrics  /usr/share/xroad-metrics/collector/scripts/cron/cron_collector.sh PROD
  30 */6  *   *   *   xroad-metrics  /usr/share/xroad-metrics/collector/scripts/cron/cron_collector.sh TEST

```

If collector is to be run only manually, comment out the default cron task:
```bash
# 15 */6 * * * xroad-metrics /usr/share/xroad-metrics/collector/scripts/cron/cron_collector.sh 
```

### Note about Indexing

Index build (see [Database module, Index Creation](database_module.md#Indexes) might affect availability of cursor for long-running queries.
Please review the need of active Collector module while running long-running queries in other modules.

## Monitoring and Status

### Logging 

The settings for the log file in the settings file are the following:

```yaml
xroad:
  instance: EXAMPLE

#  ...

logger:
  name: collector
  module: collector
  
  # Possible logging levels from least to most verbose are:
  # CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
  level: INFO

  # Logs and heartbeat files are stored under these paths.
  # Also configure external log rotation and app monitoring accordingly.
  log-path: /var/log/xroad-metrics/collector/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/xroad-metrics/collector/logs/log_collector_EXAMPLE.json`.

Every log line includes:

- **"timestamp"**: timestamp in Unix format (epoch)
- **"local_timestamp"**: timestamp in local format '%Y-%m-%d %H:%M:%S %z'
- **"module"**: "collector"
- **"version"**: in form of "v${MINOR}.${MAJOR}"
- **"activity"**: possible valuse "collector_start", "collector_worker", "collector_end"
- **level**: possible values "INFO", "WARNING", "ERROR"
- **msg**: message

In case of "activity": "collector_end", the "msg" includes values separated by comma:

- Total collected: number of Member's Security server from where the logs were collected successfully
- Total error: number of Member's Security server from where the logs were not collected due to error
- Total time: durations in the collection process in time format HH:MM:SS

The **collector module** log handler is compatible with the logrotate utility. To configure log rotation for the example setup above, create the file:

```
sudo vi /etc/logrotate.d/xroad-metrics-collector
```

and add the following content :
```
/var/log/xroad-metrics/collector/logs/log_collector_EXAMPLE.json {
    rotate 10
    size 2M
}
```

For further log rotation options, please refer to logrotate manual:

```
man logrotate
```

### Heartbeat

The settings for the heartbeat file in the settings file are the following:

```yaml
xroad:
  instance: EXAMPLE

#  ...

logger:
  #  ...
  heartbeat-path: /var/log/xroad-metrics/collector/heartbeat

```

The heartbeat file is written to `heartbeat-path` and hearbeat file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/xroad-metrics/collector/heartbeat/heartbeat_collector_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"

