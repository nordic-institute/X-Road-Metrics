
| [![Republic of Estonia Information System Authority](img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Reports Module

## About

The **Reports module** is part of [X-Road v6 monitor project](../README.md), which includes modules of [Database module](database_module.md), [Collector module](collector_module.md), [Corrector module](corrector_module.md), [Analysis module](analysis_module.md), Reports module (this document), [Opendata module](opendata_module.md) and [Networking/Visualizer module](networking_module.md).

The **Reports module** is responsible for creating monthly reports about X-Road v6 members subsystems (datasets usage).
The execution of the reports module can be either performed automatically (via **cron job**) or manually.

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in one server (different users but in same group 'opmon') but also in separate servers.  

Overall system is also designed in a way, that allows to monitor data from different X-Road v6 instances (in Estonia `ee-dev`, `ee-test`, `EE`, see also [X-Road v6 environments](https://moodle.ria.ee/mod/page/view.php?id=700).

Overall system is also designed in a way, that can be used by X-Road Centre for all X-Road members as well as for Member own monitoring (includes possibilities to monitor also members data exchange partners).

The module source code can be found at:

```
https://github.com/ria-ee/X-Road-opmonitor
```

## Diagram

TODO: add new diagram, this is outdated! OPMONDEV-63.

![reports module diagram](img/Reports_module_diagram_v6.png "Reports module diagram")

## Networking

### Outgoing
Required:
- The reports-module needs access to the Database Module (see ==> [Database_Module](database_module.md) <==).

Optional:
- The reports-module can be configured to access a reports publishing server (via rsync or scp, port 22 (SSH)).
- The reports-module can be configured to send e-mail notifications through an SMTP server to announce member/subsystem contacts about reports created and published (port 25 (SMTP)).

### Incoming

Reports-module doesn't need any **incoming** connections.

## Installation

This sections describes the necessary steps to install the **reports module** on an Ubuntu 20.04 Linux host.
To a complete overview of different modules and machines, please refer to the ==> [System Architecture](system_architecture.md) <== documentation.

### Add X-Road OpMon Package Repository for Ubuntu
TODO

### Install Reports Package
To install opmon-reports and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install opmon-reports
```

The installation package automatically installs following items:
 * opmon-reports command to run the reports module manually
 * Linux user named _opmon_ and group _opmon_
 * settings file _/etc/opmon/reports/settings.yaml_
 * cronjob in _/etc/cron.d/opmon-reports-cron_ to generate reports automatically once per month
 * log folders to _/var/log/opmon/reports/_

Only _opmon_ user can access the settings files and run opmon-reports command.

To use reports-module you need to fill in your X-Road and MongoDB configuration into the settings file.
Refer to section [Reports-module Configuration](#reports-module-configuration).

## Usage

### Reports-module Configuration

To use opmon-reports you need to fill in your X-Road and MongoDB configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/opmon/reports/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* username and password for the reports-module MongoDB user
* e-mail template, SMTP server and port

To run opmon-reports for multiple X-Road instances, a settings profile for each instance can be created. 
For example to have profiles DEV, TEST and PROD create three copies of `setting.yaml` file named 
`settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml`.
Then fill the profile specific settings to each file and use the --profile
flag when running opmon-reports. For example to run using the TEST profile:
```
opmon-reports --profile TEST reports
```

`opmon-reports` command searches the settings file first in current working direcrtory, then in
_/etc/opmon/reports/_

Available languages for the reports are:

```
en - english
et - estonian
```

Report language translation files can be found in path _/etc/opmon/reports/lang_

### Report Targets

By default Opmon Reports Module will generate a report for each subsystem that has acted as a client or producer
of at least one request during the report period. This subsystem list is fetched automatically from the Database Module.
Since this method relies solely on the operational monitoring data it has following limitations:
    
1. e-mail notifications cannot be sent for the generated reports
2. localized subsystem names are not available in the reports, only codes

The report target subsystems can be defined in full detail manually by using a xroad-descriptor json file as 
described in chapter [X-Road Descriptor File](#x-road-descriptor-file)

If you want to generate a report for a single subsystem it is also possible to use a command line argument like this:
```bash
opmon-reports report --subsystem MYCLASS:MYMEMBER:MYSUB
```

### X-Road Descriptor File

The settings.yaml file has a setting named *xroad.descriptor-path* that is blank by default. 
This can be set pointing to a file that contains a list of all X-Road subsystems that should be subject to report 
generation. The file can also contain additional information about the subsystems; currently maintainer e-mail 
addresses and localized subsystem names are supported.
 
Below is an example of a xroad-descriptor file format:

```json
[
  {
    "x_road_instance": "sample",
    "member_class": "MemberClassA",
    "member_code": "MemberCodeA",
    "subsystem_code": "SubsystemCodeA",
    "member_name": "Member Name",
    "subsystem_name": {
      "et": "Subsystem Name ET",
      "en": "Subsystem Name EN"
    },
    "email": [
      {
        "name": "Firstname Lastname",
        "email": "yourname@yourdomain"
      }
    ]
  },
  {
      "x_road_instance": "sample",
      "member_class": "MemberClassA",
      "member_code": "MemberCodeA",
      "subsystem_code": "SubsystemCodeB",
      ...
  }
]
```

The file format is based on RIHA (Estonian catalogue of public sector information systems, https://www.riha.ee) 
interfaces. Currently there is no standardized way to generate this file automatically as it contains information 
that is not available in the standard X-Road Central Server interfaces.


### Manual usage

All reports-module actions can be executed by calling the `opmon-reports` command.
Command should be executed as user `opmon` so change to that user:
```bash
sudo su opmon
```

Available actions:
```bash
opmon-reports report                       # Generate reports using default arguments
opmon-reports notify                       # Send pending e-mail notifications
opmnon-reports --help                      # Show available command line arguments
```

Above examples use the default settings file. To use another settings profile, you can use --profile flag:
```bash
opmon-reports --profile TEST report
opmon-reports --profile TEST notify
```

### Cron settings
Default installation includes a cronjob in _/etc/cron.d/opmon-reports-cron_ that runs reports-module monthly. 
This job runs reports module using the default settings profile (_/etc/opmon/reports/settings.yaml_)

It is important to note that it can take several days for ==> [Collector module](collector_module.md) <== to receive 
the operational data from security server(s) and for the ==> [Corrector_module](corrector_module.md) <== to 
clean the raw data and derive monitoring metrics in a clean database collection if the X-Road instance has a lot of members.

This means that if monthly reports are to be generated, the cron job should run **after** the collector and corrector
have finished processing data for that month. By default the cron job is configured to run on 10th day of each month,
which should allow for a long enough grace period.

If you want to change the reports cronjob scheduling or settings profiles, edit the file e.g. with vi
```
vi /etc/cron.d/opmon-reports-cron
```
and make your changes. For example to run reports every six months on the 15th day using settings profiles PROD and TEST:
```bash
# m   h  dom  mon   dow  user     command
  1   0   15   */6    *   opmon    opmon-reports --profile TEST report
  1   3   15   */6    *   opmon    opmon-reports --profile PROD report

```

If reports-generation is to be run only manually, comment out the default cron task by adding a '#'-character:
```bash
#  1   0   10   *   *   opmon    opmon-reports report
```

### Publishing Reoprts
Using default settings the opmon-reports command generates report pdf files into folder _/home/opmon/reports_.
If you want to publish the reports on some external file server, you can setup e.g. a rsync cronjob. 
Below example assumes your file-server hostname is _myfileserver_ and user _myuser_ can access it with from the
opmon-reports host.

TODO: add example when file server strategy has been confirmed. OPMONDEV-63

If you don't use any external file server users can copy the reports to their workstations using e.g. _scp_ command.
TODO: add example  

### E-mail Notifications
TODO: Add documentation after the default notification strategy has been confirmed. OPMONDEV-63


### Note about Indexing

Index build in background (see [Database module, Index Creation](database_module.md#index-creation) might affect 
availability of cursor for long-running queries.
Please review the need of active [Collector module](collector_module.md) and specifically the need of active 
[Corrector module](corrector_module.md) while running Reports.

## Monitoring and Status

### Logging 

The settings for the log file in the settings file are the following:

```yaml
xroad:
  instance: EXAMPLE

#  ...

logger:
  name: reports
  module: reports
  
  # Possible logging levels from least to most verbose are:
  # CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
  level: INFO

  # Logs and heartbeat files are stored under these paths.
  # Also configure external log rotation and app monitoring accordingly.
  log-path: /var/log/opmon/reports/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/opmon/reports/logs/log_reports_EXAMPLE.json`.

Every log line includes:

- **"timestamp"**: timestamp in Unix format (epoch)
- **"local_timestamp"**: timestamp in local format '%Y-%m-%d %H:%M:%S %z'
- **"module"**: "reports"
- **"version"**: in form of "v${MINOR}.${MAJOR}"
- **"activity"**: string identifier of the logging code block
- **level**: possible values "INFO", "WARNING", "ERROR"
- **msg**: message

The **reports module** log handler is compatible with the logrotate utility. To configure log rotation for the example setup above, create the file:

```
sudo vi /etc/logrotate.d/opmon-reports
```

and add the following content :
```
/var/log/opmon/reports/logs/log_reports_EXAMPLE.json {
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
  heartbeat-path: /var/log/opmon/reports/heartbeat

```

The heartbeat file is written to `heartbeat-path` and hearbeat file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/opmon/reports/heartbeat/heartbeat_reports_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"
