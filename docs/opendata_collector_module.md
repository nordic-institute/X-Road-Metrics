
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Opendata Collector Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The **Opendata Collector module** is part of [X-Road Metrics](../README.md),
which include following modules:
 - [Database module](./database_module.md)
 - [Collector module](./collector_module.md)
 - [Corrector module](./corrector_module.md)
 - [Reports module](./reports_module.md)
 - [Anonymizer module](./anonymizer_module.md)
 - [Opendata module](./opendata_module.md)
 - [Networking/Visualizer module](./networking_module.md)
 - [Opendata Collector module](./opendata_collector_module.md)

The **Opendata Collector module** is responsible for retrieving data from other X-Road Metrics instances and inserting into the database storage. The execution of the opendata collector module is performed automatically via a **cron job** task.

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in one server, but also in separate servers. X-Road Metrics modules are controlled by unix user 'xroad-metrics' in group 'xroad-metrics'.


## Networking

### Outgoing

- The Opendata collector module needs HTTP-access to the X-Road Metrics Opendata API to get opendata.
- The Opendata collector module needs access to the Database Module (see ==> [Database_Module](database_module.md) <==).

### Incoming

No incoming connection is needed in the Opendata collector module.

### Add X-Road Extensions Package Repository for Ubuntu
````bash
wget -qO - https://artifactory.niis.org/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository 'https://artifactory.niis.org/xroad-extensions-release-deb main'
````

The following information can be used to verify the key:
- key hash: 935CC5E7FA5397B171749F80D6E3973B
- key fingerprint: A01B FE41 B9D8 EAF4 872F A3F1 FB0D 532C 10F6 EC5B
- 3rd party key server: [Ubuntu key server](https://keyserver.ubuntu.com/pks/lookup?search=0xfb0d532c10f6ec5b&fingerprint=on&op=index)


### Install Opendata Collector Package
To install xroad-metrics-opendata-collector and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install xroad-metrics-opendata-collector
```

The installation package automatically installs following items:
 * xroad-metrics-opendata-collector command to run the opendata collector manually
 * Linux user named _xroad-metrics_ and group _xroad-metrics_
 * settings file _/etc/xroad-metrics/opendata_collector/settings.yaml_
 * opendata sources settings file _/etc/xroad-metrics/opendata_collector/opendata_sources_settings.yaml_
 * cronjob in _/etc/cron.d/xroad-metrics-opendata-collector-cron_ to run opendata collector automatically
 * log folders to _/var/log/xroad-metrics/opendata_collector/_

Only _xroad-metrics_ user can access the settings files and run xroad-metrics-opendata-collector command.

To use opendata collector you need to fill in your X-Road and MongoDB configuration into the settings file first.
Fill _opendata_sources_settings.yaml_ and _/etc/cron.d/xroad-metrics-opendata-collector-cron_ to fetch opendata.
Refer to section [Opendata Collector Configuration](#opendata-collector-configuration)


## Usage
### Opendata Collector Configuration

Before using the opendata collector module, make sure you have installed and configured the [Database_Module](database_module.md)
and created the MongoDB credentials.

To use opendata collector you need to fill in your X-Road and MongoDB configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/xroad-metrics/opendata_collector/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* MongoDB host
* username and password for the collector module MongoDB user

To run opendata collector for multiple X-Road instances, a settings profile for each instance can be created. For example to have profiles DEV, TEST and PROD create three copies of `setting.yaml`
file named `settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml`.
Then fill the profile specific settings to each file and use the --profile
flag when running xroad-metrics-opendata-collector.

```bash
sudo vi /etc/xroad-metrics/opendata_collector/opendata_sources_settings.yaml
```

This settings file is used to configure X-Road instances to fetch Opendata from.
Settings that user must fill in:

* X-Road instance name. This is mandatory key of X-Road instance setting.
* Opendata API harvest endpoint url. This is mandatory setting.
* Number of max Opendata items in single response. Mandatory field.
* Starting date and time to fetch Opendata from. Mandatory field.
* Ending date and time to fetch Opendata until
* Timezone offset of Opendata API
* Should SSL verification be done during request to Opendata API

Configuration example:

```yaml
PLAYGROUND-TEST:
  url: https://playground-example/api/harvest
  limit: 2000
  from_dt: '2022-12-05T00:00:00'
  opendata_api_tz_offset: '+0200'
  verify_ssl: False
PLAYWAY-TEST:
  url: https://playway-example/api/harvest
  limit: 5000
  from_dt: '2022-12-05T00:00:00'
  until_dt: '2023-04-30T00:00:00'
  opendata_api_tz_offset: # defaults to +0000
  verify_ssl: True
```

For example to run opendata collector with TEST profile
```
xroad-metrics-opendata-collector --profile TEST PLAYGROUND-TEST
```

### Cron settings
Default installation includes empty cronjob in _/etc/cron.d/xroad-metrics-opendata-collector-cron_ .

If you want to change the opendata collector cronjob scheduling or settings profiles, edit the file e.g. with vi

```bash
vi /etc/cron.d/xroad-metrics-opendata-collector-cron
```
and make your changes. For example to run opendata collector every six hours using settings profiles PROD and TEST:

```bash
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# m   h  dom mon dow  user       command
  15 */6  *   *   *   xroad-metrics  xroad-metrics-opendata-collector --profile PROD PLAYGROUND-TEST
  30 */6  *   *   *   xroad-metrics  xroad-metrics-opendata-collector --profile TEST PLAYWAY-TEST

```
## Opendata Anonymization

Opendata collector fetches opendata as module's name suggests.
We want to be sure completely, that data does not contain any sensitive information.
What is treated as sensitive information may differ depending on country data was collected and processed.
Please refer to section [Opendata Anonymization](anonymizer_module.md#opendata-anonymization)

## Monitoring and Status

### Logging

The settings for the log file in the settings file are the following:

```yaml
xroad:
  instance: EXAMPLE

#  ...

logger:
  name: opendata-collector
  module: opendata-collector

  # Possible logging levels from least to most verbose are:
  # CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
  level: INFO

  # Logs and heartbeat files are stored under these paths.
  # Also configure external log rotation and app monitoring accordingly.
  log-path: /var/log/xroad-metrics/opendata_collector/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name.
The above example configuration would write logs to `/var/log/xroad-metrics/opendata_collector/logs/log_collector_EXAMPLE.json`.

Every log line includes:

- **"timestamp"**: timestamp in Unix format (epoch)
- **"local_timestamp"**: timestamp in local format '%Y-%m-%d %H:%M:%S %z'
- **"module"**: "opendata-collector"
- **"version"**: in form of "v${MINOR}.${MAJOR}"
- **"activity"**: possible values "get_opendata", "params_preparation_failed", "get_opendata_connection_failed", "get_opendata_main_failed"
- **level**: possible values "INFO", "WARNING", "ERROR"
- **msg**: message

The **opendata-collector module** log handler is compatible with the logrotate utility. To configure log rotation for the example setup above, create the file:

```
sudo vi /etc/logrotate.d/xroad-metrics-opendata-collector
```

and add the following content :
```
/var/log/xroad-metrics/opendata_collector/logs/log_collector_EXAMPLE.json {
    rotate 10
    size 2M
}
```

For further log rotation options, please refer to logrotate manual:

```
man logrotate
```