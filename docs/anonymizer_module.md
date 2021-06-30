
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Anonymizer Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The **Anonymizer module** is part of [X-Road Metrics](../README.md), 
which include following modules:
 - [Database module](../database_module.md)
 - [Collector module](../collector_module.md)
 - [Corrector module](../corrector_module.md) 
 - [Reports module](../reports_module.md) 
 - [Anonymizer module](../anonymizer_module.md)
 - [Opendata module](../opendata_module.md) 
 - [Networking/Visualizer module](../networking_module.md)

The **Anonymizer module** is responsible of preparing the operational monitoring data for publication through 
the [Opendata module](opendata_module.md). Anonymizer configuration allows opmon extension administrator to set 
fine-grained rules for excluding whole opmon records or to modify selected data fields before the data is published.

The anonymizer module uses the opmon data that [Corrector module](corrector_module.md) has prepared and stored 
to MongoDb as input. The anonymizer processes the data using the configured ruleset and stores the output to the
opendata PostgreSQL database for publication.

## Architecture

Anonymizer prepares data for the opendata module. Overview of the module architecture related to publishing opmon data
through  [Opendata module](opendata_module.md) is diagram below:
 ![system diagram](img/opendata/opendata_overview.png "System overview")

## Networking

MongoDb is used to store "non-anonymized" opmon data that should be accessible only by the X-Road administrators.
Anonymized opmon data that can be published for wider audience is stored in the PostgreSQL. The opendata UI needs
access only to the PostgreSQL. To follow the "principal of least priviledge" it is recommended to
install opmon UI on a dedicated host that has no access at all to MongoDb.
However, the Anonymizer module needs access also to the "not-public" data so it should
run on a host that has access to both MongoDb and PostgreSQL.

The anonymizer module provides no incoming network interfaces.

## Installation

This sections describes the necessary steps to install the **anonymizer module** on 
an Ubuntu 20.04 Linux host. For a complete overview of different modules and machines, 
please refer to the ==> [System Architecture](system_architecture.md) <== documentation.


### Add X-Road OpMon Package Repository for Ubuntu
TODO

### Install Anonymizer Package
To install opmon-anonymizer and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install opmon-anonymizer
```

The installation package automatically installs following items:
 * opmon-anonymizer command
 * Linux user named _opmon_ and group _opmon_
 * configuration files: 
   * _/etc/opmon/anonymizer/settings.yaml_
   * _/etc/opmon/anonymizer/field_data.yaml_
   * _/etc/opmon/anonymizer/field_translations.yaml_
 * cron job _/etc/cron.d/opmon-anonymizer-cron_ to run anonymizer periodically
 * log folders to _/var/log/opmon/anonymizer/_

Only _opmon_ user can access the settings files and run opmon-anonymizer command.

To use corrector you need to fill in your X-Road, MongoDb and PostgreSQL configuration into the settings file.
Next chapter has detailed instructions on how to configure the anonymizer module.

## Usage

### Anonymizer General Settings

To use anonymizer you need to fill in your X-Road, MongoDB and PostgreSQL configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/opmon/corrector/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* mongodb host
* username and password for the anonymizer module MongoDB user
* host and port of the PostgreSQL server
* username and password for anonymizer postgreSQL user
* name of PostgreSQL database where to store the anonymized data
* list of PostgreSQL users that should have read-only access to the anonymized data

The read-only PostgrSQL users should be the users that Opendata-UI and Networking modules use to read data from the
PostgreSQL.


### Configuration of _Hiding Rules_

Anonymizer can be configured to hide (exclude) whole data records from the open-data set by defining _hiding rules_ in
_settings.yaml_ file.

A hiding rule consists of list of feature - regular expression pairs. If the contents of the field matches the regex,
then the record is excluded from opendata set.

A typical example is to exclude all opmon data records related to specific clients, services or member types. 
The example below defines two hiding rules. 
First rule will exclude all records where client id is _"foo"_ **and** service id is _"bar"_.
The second rule will exclude all records where service member class is not _"GOV"_.

```yaml
# settings.yaml
anonymizer:
  
  ...
  
  hiding-rules:
    -
      - feature: 'clientMemberCode'
        regex: '^(foo)$'
      - feature: 'serviceMemberCode'
        regex: '^(bar)$'

    -
      - feature: 'serviceMemberClass'
        regex: '^(?!GOV$).*$'
```

### Configuration of Substitution Rules
Anonymizer can be configured to substitute the values of selected fields in the opendata set for 
records that fulfill a set of conditions. These _substitution rules_ are defined in _settings.yaml_ file.

A substitution rule has two parts. First *conditions* has a set of rules that defines the set of records
where the substitution applies. These conditions have same format as the _hiding rules_ above.
Second, there is the *subtitutions* part that consists of feature-value pairs, where feature is the name of the field
to be substituted and value contains the substitute string.

The below example defines two substitution rules.
First rule will substitute client and service member codes with _"N/A"_ if the client member code is _"foo2"_.
The second rule will substitute message id with 0, if client member code is _"bar2"_ and 
service member code is _"foo2"_.

```yaml
# settings.yaml
anonymizer:
  
  ...

  substitution-rules:
    - conditions:
        - feature: 'clientMemberCode'
          regex: '^foo2$'

      substitutes:
        - feature: 'clientMemberCode'
          value: 'N/A'
        - feature: 'serviceMemberCode'
          value: 'N/A'

    - conditions:
        - feature: 'clientMemberCode'
          regex: '^bar2$'
        - feature: 'clientMemberCode'
          regex: '^foo2$'

      substitutes:
        - feature: 'messageId'
          value: '0'
```

### Settings Profiles
To run anonymizer for multiple X-Road instances, a settings profile for each instance can be created. 
For example to have profiles DEV, TEST and PROD create three copies of `setting.yaml` 
file named `settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml`.
Then fill the profile specific settings to each file and use the --profile
flag when running opmon-anonymizer. For example to run anonymizer manually using the TEST profile:
```
opmon-correctord --profile TEST
```

`opmon-anonymizer` command searches the settings file first in current working direcrtory, then in
_/etc/opmon/anonymizer/_

### Manual usage

All anonymizer module can be executed by calling the `opmon-anonymizer` command.
Command should be executed as user `opmon` so change to that user:
```bash
sudo su opmon
```

Currently following command line arguments are supported:
```bash
opmon-anonymizer --help                     # Show description of the command line argumemts
opmon-anonymizer --limit <number>           # Optional flag to limit the number of records to process. 
opmon-anonymizer --profile <profile name>   # Run with a non-default settings profile
```


### Cron settings
Default installation includes a cronjob in _/etc/cron.d/opmon-anonymizer-cron_ that runs anonymizer monthly. 
This job runs anonymizer using default settings profile (_/etc/opmon/collector/settings.yaml_)

If you want to change the collector cronjob scheduling or settings profiles, edit the file e.g. with vi
```
vi /etc/cron.d/opmon-anonymizer-cron
```
and make your changes. For example to run collector bi-weekly using settings profiles PROD and TEST:
```bash
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# m   h  dom    mon dow  user       command
  15  30  1,15   *   *   opmon      opmon-anonymizer --profile TEST
  16  15  1,15   *   *   opmon      opmon-anonymizer --profile PROD

```

If collector is to be run only manually, comment out the default cron task:
```bash
# 15 30 15 * * opmon opmon-anonymizer
```

## Monitoring and Status

### Logging 

The settings for the log file in the settings file are the following:

```yaml
xroad:
  instance: EXAMPLE

#  ...

logger:
  name: anonymizer
  module: anonymizer
  
  # Possible logging levels from least to most verbose are:
  # CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
  level: INFO

  # Logs and heartbeat files are stored under these paths.
  # Also configure external log rotation and app monitoring accordingly.
  log-path: /var/log/opmon/anonymizer/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/opmon/collector/logs/log_collector_EXAMPLE.json`.


The **anonymizer module** log handler is compatible with the logrotate utility. 
To configure log rotation for the example setup above, create the file:

```
sudo vi /etc/logrotate.d/opmon-anonymizer
```

and add the following content :
```
/var/log/opmon/collector/logs/log_anonymizer_EXAMPLE.json {
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
  heartbeat-path: /var/log/opmon/anonymizer/heartbeat

```

The heartbeat file is written to `heartbeat-path` and hearbeat file name contains the X-Road instance name. 
The above example configuration would write logs to
 `/var/log/opmon/anonymizer/heartbeat/heartbeat_anonymizer_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"
