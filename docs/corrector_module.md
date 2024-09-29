
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Corrector Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The **Corrector module** is part of [X-Road Metrics](../README.md), which includes the following modules:
 - [Database module](./database_module.md)
 - [Collector module](./collector_module.md)
 - [Corrector module](./corrector_module.md)
 - [Reports module](./reports_module.md)
 - [Anonymizer module](./anonymizer_module.md)
 - [Opendata module](./opendata_module.md)
 - [Networking/Visualizer module](./networking_module.md)
 - [Opendata Collector module](./opendata_collector_module.md)

The **Corrector module** is responsible to clean the raw data from corrector and derive monitoring metrics in a clean database collection. The execution of the corrector module is performed automatically via a **service** task.

It is important to note that it can take up to 7 days for the [Collector module](collector_module.md) to receive X-Road operational data from (all available) Security Server(s) and up to 3 days for the Corrector_module to clean the raw data and derive monitoring metrics in a clean database collection.

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in one server (different users but in same group 'xroad-metrics') but also in separate servers.

Overall system is also designed in a way, that allows to monitor data from different X-Road instances (e.g. in Estonia there are three instances: `ee-dev`, `ee-test` and `EE`.)

Overall system is also designed in a way, that can be used by X-Road Centre for all X-Road members as well as for Member own monitoring (includes possibilities to monitor also members data exchange partners).

The module source code can be found at:


## Diagram

![corrector module diagram](img/Corrector_module_diagram_v2.svg "Corrector module diagram")

## Pair matching logic
The first step is to add the missing fields into the document (in case it is missing some).
The value will be `None` for the missing fields.
The fields that MUST be there for each document are the following:

```yaml
# sorted alphabetically
- clientMemberClass
- clientMemberCode
- clientSecurityServerAddress
- clientSubsystemCode
- clientXRoadInstance

- messageId
- messageIssue
- messageProtocolVersion
- messageUserId
- monitoringDataTs
- representedPartyClass
- representedPartyCode

- requestAttachmentCount
- requestInTs
- requestMimeSize
- requestOutTs
- requestSoapSize

- responseAttachmentCount
- responseInTs
- responseMimeSize
- responseOutTs
- responseSoapSize

- securityServerInternalIp
- securityServerType

- serviceCode
- serviceMemberClass
- serviceMemberCode
- serviceSecurityServerAddress
- serviceSubsystemCode
- serviceVersion
- serviceXRoadInstance

- soapFaultCode
- soapFaultString
- succeeded
```

Before finding a match, a hash is calculated for the current document. The following fields are included:

```yaml
# sorted alphabetically
- clientMemberClass
- clientMemberCode
- clientSecurityServerAddress
- clientSubsystemCode
- clientXRoadInstance

- messageId
- messageIssue
- messageProtocolVersion
- messageUserId
- monitoringDataTs
- representedPartyClass
- representedPartyCode

- requestAttachmentCount
- requestInTs
- requestMimeSize
- requestOutTs
- requestSoapSize

- responseAttachmentCount
- responseInTs
- responseMimeSize
- responseOutTs
- responseSoapSize

- securityServerInternalIp
- securityServerType

- serviceCode
- serviceMemberClass
- serviceMemberCode
- serviceSecurityServerAddress
- serviceSubsystemCode
- serviceVersion
- serviceXRoadInstance

- soapFaultCode
- soapFaultString
- succeeded
```

The fields excluded from the hash are the following:

```yaml
- _id
- corrected
- insertTime
```

After calculating the hash it is checked that the hash doesn't already exist in the DB (`clean_data`).
If it does exist, the document is skipped.

If the hash doesn't exist, then possible matches are queried for the document.
The possible matches are queried using the following rules:
* `messageId` == currentDocument's messageId
* `correctorStatus` == `processing`
* (currentDoc's `requestInTs` - 60s) <= `requestInTs` <= (currentDoc's `requestInTs` + 60s)
* If the current document's `securityServerType` == `Client` then we query only the documents that have `clientHash` == `None`
If the current document's `securityServerType` == `Producer` then we query only the documents that have `producerHash` == `None`

Then all the possible candidates will be first matched using regular match to make up the pair.
The `requestInTs` time difference must be <= 60 seconds for BOTH the regular and orphan match.
The fields that must be equal for regular match are the following:

```yaml
# sorted alphabetically
- clientAttachmentCount
- clientMemberClass
- clientMemberCode
- clientSecurityServerAddress
- clientSubsystemCode
- clientXRoadInstance

- messageId
- messageIssue
- messageProtocolVersion
- messageUserId
- representedPartyClass
- representedPartyCode

- requestAttachmentCount
- requestMimeSize
- requestSoapSize

- responseAttachmentCount
- responseMimeSize
- responseSoapSize

- serviceCode
- serviceMemberClass
- serviceMemberCode
- serviceSecurityServerAddress
- serviceSubsystemCode
- serviceVersion
- serviceXRoadInstance

- soapFaultCode
- soapFaultString
- succeeded
```

If no match is found, then the orphan match will be used.
The fields that must be equal for orphan match are the following:

```yaml
# sorted alphabetically
- clientMemberClass
- clientMemberCode
- clientSecurityServerAddress
- clientSubsystemCode
- clientXRoadInstance

- messageId
- messageIssue
- messageProtocolVersion
- messageUserId
- representedPartyClass
- representedPartyCode

- serviceCode
- serviceMemberClass
- serviceMemberCode
- serviceSecurityServerAddress
- serviceSubsystemCode
- serviceVersion
- serviceXRoadInstance

- soapFaultCode
- soapFaultString
- succeeded 
```

If still no match found then the document will be added into the clean_data as `orphan`.

If the match was found then the documents will be paired and added into the clean_data as either `regular_pair` or `orphan_pair`.


## Networking

### Outgoing

The corrector module needs access to the Database Module (see ==> [Database_Module](database_module.md) <==).

### Incoming

No **incoming** connection is needed in the corrector module.

## Installation

This sections describes the necessary steps to install the **corrector module** on a Ubuntu 20.04 or Ubuntu 22.04 Linux host. For a complete overview of different modules and machines, please refer to the ==> [System Architecture](system_architecture.md) <== documentation.


### Add X-Road Extensions Package Repository for Ubuntu
````bash
wget -qO - https://artifactory.niis.org/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository 'https://artifactory.niis.org/xroad-extensions-release-deb main'
````

The following information can be used to verify the key:
- key hash: 935CC5E7FA5397B171749F80D6E3973B
- key fingerprint: A01B FE41 B9D8 EAF4 872F A3F1 FB0D 532C 10F6 EC5B
- 3rd party key server: [Ubuntu key server](https://keyserver.ubuntu.com/pks/lookup?search=0xfb0d532c10f6ec5b&fingerprint=on&op=index)

### Install Corrector Package
To install xroad-metrics-corrector and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install xroad-metrics-corrector
```

The installation package automatically installs following items:
 * `xroad-metrics-correctord` daemon
 * Linux user named _xroad-metrics_ and group _xroad-metrics_
 * settings file _/etc/xroad-metrics/corrector/settings.yaml_
 * systemd service unit configuration _/lib/systemd/system/xroad-metrics-corrector.service_
 * log folders to _/var/log/xroad-metrics/corrector/_

Only _xroad-metrics_ user can access the settings files and run xroad-metrics-correctord command.

To use corrector you need to fill in your X-Road and MongoDB configuration into the settings file.
Then you corrector daemon can be run manually or as a systemd service. Next chapter provides detailed instructions about corrector configuration and usage.

## Usage

### Corrector Configuration

Before configuring the Corrector module, make sure that you have installed and configured the [Database_Module](database_module.md)
and created the MongoDB credentials.

To use corrector you need to fill in your X-Road and MongoDB configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/xroad-metrics/corrector/settings.yaml
```
> [!TIP]  
> For a complete list of available settings, please refer to this [settings.yaml](../corrector_module/etc/settings.yaml) template file.

Settings that the user must fill in:
* X-Road instance name
* mongodb host
* username and password for the corrector module MongoDB user

### Settings Profiles
To run corrector for multiple X-Road instances, a settings profile for each instance can be created.
1. To have profiles `DEV`, `TEST`, and `PROD` create three copies of `setting.yaml`
file named `settings_DEV.yaml`, `settings_TEST.yaml`, and `settings_PROD.yaml`.
2. Fill the profile specific settings to each file 
3. Use the `--profile` flag when running `xroad-metrics-correctord`.   
   For example to run corrector manually using the TEST profile:
   ```bash
   xroad-metrics-correctord --profile TEST
   ```
> [!IMPORTANT]  
> `xroad-metrics-corrector` command searches the settings file first in current working directory, then in
`/etc/xroad-metrics/corrector/`

### Manual usage

Corrector operation can be tested by running the corrector daemon manually. For production use, it is recommended to set up a systemd service (see next chapter).

Make sure the corrector is not running as a systemd service with:

```bash
sudo systemctl stop xroad-metrics-corrector
systemctl status xroad-metrics-corrector
```

To run corrector manually in the foreground as xroad-metrics user, just execute:

```bash
xroad-metrics-correctord
```

> [!Note]
> - Corrector module has a current limit of documents controlled by `CORRECTOR_DOCUMENTS_LIMIT` (by default set to `CORRECTOR_DOCUMENTS_LIMIT` = `20000`) to ensure RAM and CPU is not overloaded during calculations.
> - The `CORRECTOR_DOCUMENTS_LIMIT` defines the processing batch size, and is executed continuously until the total of documents left is smaller than `CORRECTOR_DOCUMENTS_MIN` documents (default set to `CORRECTOR_DOCUMENTS_MIN` = `1`). 
> - The estimated amount of memory per processing batch is indicated at [System Architecture](system_architecture.md) documentation.

### systemd Service

#### Default Settings Profile

To run the corrector as a continuous background service under systemd execute the following commands:
```bash
sudo systemctl enable xroad-metrics-corrector
sudo systemctl start xroad-metrics-corrector
```

To check the service status:
```bash
systemctl status xroad-metrics-corrector
```

#### Multiples Settings Profiles

To run corrector as a systemd service using a specific settings profile you need to create a service configuration.
For example to create a service using `PROD` profile, the default service configuration can be used as a starting point:
```bash
sudo cp  /lib/systemd/system/xroad-metrics-corrector.service /lib/systemd/system/xroad-metrics-corrector-PROD.service
```

Then edit the config file e.g. with vi
```bash
sudo vi /lib/systemd/system/xroad-metrics-corrector-PROD.service
```

Modify the `ExecStart` line in the config file to use the wanted settings profile (`PROD` in this example):
```bash
ExecStart=/usr/bin/xroad-metrics-correctord --profile PROD
```

Enable and start the new service:
```bash
sudo systemctl enable xroad-metrics-corrector-PROD
sudo systemctl start xroad-metrics-corrector-PROD
```

To check the service status:
```bash
systemctl status xroad-metrics-corrector-PROD
```


### Note about Indexing

Index build (see [Database module, Index Creation](database_module.md#index-creation) might affect availability of cursor for long-running queries.
Please review the need of active Corrector module while running long-running queries in other modules.

## Monitoring and Status

### Logging

The settings for the log file in the settings file are the following:

```yaml
xroad:
  instance: EXAMPLE

#  ...

logger:
  name: corrector
  module: corrector

  # Possible logging levels from least to most verbose are:
  # CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
  level: INFO

  # Logs and heartbeat files are stored under these paths.
  # Also configure external log rotation and app monitoring accordingly.
  log-path: /var/log/xroad-metrics/corrector/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name.
The above example configuration would write logs to `/var/log/xroad-metrics/collector/logs/log_corrector_EXAMPLE.json`.

Every log line includes:

- **"timestamp"**: timestamp in Unix format (epoch)
- **"local_timestamp"**: timestamp in local format '%Y-%m-%d %H:%M:%S %z'
- **"module"**: "corrector"
- **"version"**: in form of "v${MINOR}.${MAJOR}"
- **"activity"**: possible values "corrector_main", "corrector_batch_run", "corrector_batch_start", "corrector_batch_raw", "DatabaseManager.get_raw_documents", "corrector_batch_update_timeout", "corrector_batch_update_old_to_done", "corrector_batch_remove_duplicates_from_raw", "corrector_batch_end"
- **level**: possible values "INFO", "WARNING", "ERROR"
- **msg**: message

In case of "activity": "corrector_batch_end", the "msg" includes values separated by pipe ('|'):

- Number of duplicates
- Documents processed
- Processing time: durations in the collection process in time format HH:MM:SS

The **corrector module** log handler is compatible with the logrotate utility. To configure log rotation for the example setup above, create the file:

```bash
sudo vi /etc/logrotate.d/xroad-metrics-corrector
```

and add the following content :
```
/var/log/xroad-metrics/corrector/logs/log_corrector_EXAMPLE.json {
    rotate 10
    size 2M
}
```

For further log rotation options, please refer to logrotate manual:

```bash
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
  heartbeat-path: /var/log/xroad-metrics/corrector/heartbeat

```

The heartbeat file is written to `heartbeat-path` and heartbeat file name contains the X-Road instance name.
The above example configuration would write logs to `/var/log/xroad-metrics/corrector/heartbeat/heartbeat_corrector_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"
