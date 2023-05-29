
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Anonymizer Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The **Anonymizer module** is part of [X-Road Metrics](../README.md),
which include following modules:
 - [Database module](./database_module.md)
 - [Collector module](./collector_module.md)
 - [Corrector module](./corrector_module.md)
 - [Reports module](./reports_module.md)
 - [Anonymizer module](./anonymizer_module.md)
 - [Opendata module](./opendata_module.md)
 - [Networking/Visualizer module](./networking_module.md)
 - [Opendata Collector module](./opendata_collector_module.md)

The **Anonymizer module** is responsible of preparing the operational monitoring data for publication through
the [Opendata module](opendata_module.md). Anonymizer configuration allows X-Road Metrics extension administrator to set
fine-grained rules for excluding whole operatinal monitoring data records or to modify selected data fields before the data is published.

The anonymizer module uses the operational monitoring data that [Corrector module](corrector_module.md) has prepared and stored
to MongoDb as input. The anonymizer processes the data using the configured ruleset and stores the output to the
opendata PostgreSQL database for publication.

## Architecture

Anonymizer prepares data for the Opendata module. Overview of the module architecture related to publishing operational monitoring data
through  [Opendata module](opendata_module.md) is diagram below:
 ![system diagram](img/opendata/opendata_overview.png "System overview")

## Networking

MongoDb is used to store "non-anonymized" operational monitoring data that should be accessible only by the X-Road Metrics administrators.
Anonymized operational monitoring data that can be published for wider audience is stored in the PostgreSQL. The Opendata UI needs
access only to the PostgreSQL. To follow the "principal of least priviledge" it is recommended to
install Opendata UI on a dedicated host that has no access at all to MongoDb.
However, the Anonymizer module needs access also to the "not-public" data, so it should
run on a host that has access to both MongoDb and PostgreSQL.

The anonymizer module provides no incoming network interfaces.

## Database (PostgreSQL) setup

See [Opendata database](opendata_module.md)

### Establish encrypted SSL/TLS client connection

For a connection to be known SSL-secured, SSL usage must be configured on both the client and the server before the connection is made.
If it is only configured on the server, the client may end up sending sensitive information before it knows that the server requires high security.

To ensure secure connections `ssl-mode` and `ssl-root-cert` parameterers has to be provided in settings file.
Possible values for `ssl-mode`: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`
For detailed information see https://www.postgresql.org/docs/current/libpq-ssl.html

To configure path to the SSL root certificate, set `ssl-root-cert`

Example of `/etc/settings.yaml` entry:
```
postgres:
  host: localhost
  port: 5432
  user: postgres
  password: *******
  database-name: postgres
  table-name: logs
  ssl-mode: verify-full
  ssl-root-cert: /etc/ssl/certs/root.crt
```

## Installation

This sections describes the necessary steps to install the **anonymizer module** on
an Ubuntu 20.04 or Ubuntu 22.04 Linux host. For a complete overview of different modules and machines,
please refer to the ==> [System Architecture](system_architecture.md) <== documentation.


### Add X-Road Extensions Package Repository for Ubuntu
````bash
wget -qO - https://artifactory.niis.org/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository 'https://artifactory.niis.org/xroad-extensions-release-deb main'
````

The following information can be used to verify the key:
- key hash: 935CC5E7FA5397B171749F80D6E3973B
- key fingerprint: A01B FE41 B9D8 EAF4 872F A3F1 FB0D 532C 10F6 EC5B
- 3rd party key server: [Ubuntu key server](https://keyserver.ubuntu.com/pks/lookup?search=0xfb0d532c10f6ec5b&fingerprint=on&op=index)

### Install Anonymizer Package
To install xroad-metrics-anonymizer and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install xroad-metrics-anonymizer
```

The installation package automatically installs following items:
 * xroad-metrics-anonymizer command
 * Linux user named _xroad-metrics_ and group _xroad-metrics_
 * configuration files:
   * _/etc/xroad-metrics/anonymizer/settings.yaml_
   * _/etc/xroad-metrics/anonymizer/field_data.yaml_
   * _/etc/xroad-metrics/anonymizer/field_translations.yaml_
 * cron job _/etc/cron.d/xroad-metrics-anonymizer-cron_ to run anonymizer periodically
 * log folders to _/var/log/xroad-metrics/anonymizer/_

Only _xroad-metrics_ user can access the settings files and run xroad-metrics-anonymizer command.

To use corrector you need to fill in your X-Road, MongoDb and PostgreSQL configuration into the settings file.
Next chapter has detailed instructions on how to configure the anonymizer module.

## Usage

### Anonymizer General Settings

Before configuring the Anonymizer module, make sure you have done the following:
- installed and configured the [Database_Module](database_module.md)
- created the MongoDB user accounts
- installed and configured the [Opendata database](opendata_module.md)
- created the Opendata database user accounts

To use anonymizer you need to fill in your X-Road, MongoDB and PostgreSQL configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/xroad-metrics/anonymizer/settings.yaml
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

A typical example is to exclude all operational monitoring data records related to specific clients, services or member types.
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
flag when running xroad-metrics-anonymizer. For example to run anonymizer manually using the TEST profile:
```
xroad-metrics-anonymizer --profile TEST
```

`xroad-metrics-anonymizer` command searches the settings file first in current working direcrtory, then in
_/etc/xroad-metrics/anonymizer/_

### Manual usage

All anonymizer module can be executed by calling the `xroad-metrics-anonymizer` command.
Command should be executed as user `xroad-metrics` so change to that user:
```bash
sudo su xroad-metrics
```

Currently following command line arguments are supported:
```bash
xroad-metrics-anonymizer --help                     # Show description of the command line argumemts
xroad-metrics-anonymizer --limit <number>           # Optional flag to limit the number of records to process.
xroad-metrics-anonymizer --profile <profile name>   # Run with a non-default settings profile
```


### Cron settings
Default installation includes a cronjob in _/etc/cron.d/xroad-metrics-anonymizer-cron_ that runs anonymizer monthly.
This job runs anonymizer using default settings profile (_/etc/xroad-metrics/collector/settings.yaml_)

If you want to change the collector cronjob scheduling or settings profiles, edit the file e.g. with vi
```
vi /etc/cron.d/xroad-metrics-anonymizer-cron
```
and make your changes. For example to run collector bi-weekly using settings profiles PROD and TEST:
```bash
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# m   h  dom    mon dow  user       command
  15  30  1,15   *   *   xroad-metrics      xroad-metrics-anonymizer --profile TEST
  16  15  1,15   *   *   xroad-metrics      xroad-metrics-anonymizer --profile PROD

```

If collector is to be run only manually, comment out the default cron task:
```bash
# 15 30 15 * * xroad-metrics xroad-metrics-anonymizer
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
  log-path: /var/log/xroad-metrics/anonymizer/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name.
The above example configuration would write logs to `/var/log/xroad-metrics/anonymizer/logs/log_anonymizer_EXAMPLE.json`.


The **anonymizer module** log handler is compatible with the logrotate utility.
To configure log rotation for the example setup above, create the file:

```
sudo vi /etc/logrotate.d/xroad-metrics-anonymizer
```

and add the following content :
```
/var/log/xroad-metrics/anonymizer/logs/log_anonymizer_EXAMPLE.json {
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
  heartbeat-path: /var/log/xroad-metrics/anonymizer/heartbeat

```

The heartbeat file is written to `heartbeat-path` and hearbeat file name contains the X-Road instance name.
The above example configuration would write logs to
 `/var/log/xroad-metrics/anonymizer/heartbeat/heartbeat_anonymizer_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"
