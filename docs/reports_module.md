
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Reports Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The **Reports module** is part of [X-Road Metrics](../README.md), which includes the following modules:
 - [Database module](./database_module.md)
 - [Collector module](./collector_module.md)
 - [Corrector module](./corrector_module.md)
 - [Reports module](./reports_module.md)
 - [Anonymizer module](./anonymizer_module.md)
 - [Opendata module](./opendata_module.md)
 - [Networking/Visualizer module](./networking_module.md)
 - [Opendata Collector module](./opendata_collector_module.md)

The **Reports module** is responsible for creating monthly reports about subsystems of X-Road members (datasets usage).
The execution of the reports module can be either performed automatically (via **cron job**) or manually.

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in
one server (different users but in same group 'xroad-metrics') but also in separate servers.

Overall system is also designed in a way, that allows to monitor data from different X-Road instances
(e.g. in Estonia there are three instances: `ee-dev`, `ee-test` and `EE`.)

Overall system is also designed in a way, that can be used by X-Road Centre for all X-Road members as well as for
Member own monitoring (includes possibilities to monitor also members data exchange partners).


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

This sections describes the necessary steps to install the **reports module** on an Ubuntu 20.04 or Ubuntu 22.04 Linux host.
To a complete overview of different modules and machines, please refer to the ==> [System Architecture](system_architecture.md) <== documentation.

### Add X-Road Extensions Package Repository for Ubuntu
````bash
wget -qO - https://artifactory.niis.org/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository 'https://artifactory.niis.org/xroad-extensions-release-deb main'
````

The following information can be used to verify the key:
- key hash: `935CC5E7FA5397B171749F80D6E3973B`
- key fingerprint: `A01B FE41 B9D8 EAF4 872F A3F1 FB0D 532C 10F6 EC5B`
- 3rd party key server: [Ubuntu key server](https://keyserver.ubuntu.com/pks/lookup?search=0xfb0d532c10f6ec5b&fingerprint=on&op=index)


### Install Reports Package
To install xroad-metrics-reports and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install xroad-metrics-reports
```

The installation package automatically installs following items:
 * xroad-metrics-reports command to run the reports module manually
 * Linux user named _xroad-metrics_ and group _xroad-metrics_
 * settings file _/etc/xroad-metrics/reports/settings.yaml_
 * cronjob in _/etc/cron.d/xroad-metrics-reports-cron_ to generate reports automatically once per month
 * log folders to _/var/log/xroad-metrics/reports/_

Only _xroad-metrics_ user can access the settings files and run xroad-metrics-reports command.

To use reports-module you need to fill in your X-Road and MongoDB configuration into the settings file.
Refer to section [Reports-module Configuration](#reports-module-configuration).

## Usage

### Reports-module Configuration

Before configuring the Reports module, make sure you have installed and configured the [Database_Module](database_module.md)
and created the MongoDB credentials.

To use xroad-metrics-reports you need to fill in your X-Road and MongoDB configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/xroad-metrics/reports/settings.yaml
```
> [!TIP]  
> For a complete list of available settings, please refer to this [settings.yaml](../reports_module/etc/settings.yaml) template file.

Settings that the user must fill in:
* X-Road instance name
* username and password for the reports-module MongoDB user
* e-mail template, SMTP server and port

### Settings Profiles

To run xroad-metrics-reports for multiple X-Road instances, a settings profile for each instance can be created.
1. To have profiles `DEV`, `TEST`, and `PROD` create three copies of `setting.yaml`
file named `settings_DEV.yaml`, `settings_TEST.yaml`, and `settings_PROD.yaml`.
2. Fill the profile specific settings to each file 
3. Use the `--profile` flag when running `xroad-metrics-reports`.   
   For example to run reports manually using the TEST profile:
   ```bash
   xroad-metrics-reports --profile TEST report
   ```
> [!IMPORTANT]  
> `xroad-metrics-reports` command searches the settings file first in current working directory, then in
`/etc/xroad-metrics/reports/`

Available languages for the reports are:

| Code | Language  |
|------|-----------|
| en   | English   |
| et   | Estonian  |


Report language translation files can be found in path `/etc/xroad-metrics/reports/lang`

> [!TIP]  
> Sample translation files can be found [here](../reports_module/etc/lang/).

### Report Targets

By default the Reports Module will generate a report for each subsystem that has acted as a client or producer
of at least one request during the report period. This subsystem list is fetched automatically from the Database Module.
Since this method relies solely on the operational monitoring data it has following limitations:

1. e-mail notifications cannot be sent for the generated reports
2. localized subsystem names are not available in the reports, only codes

The report target subsystems can be defined in full detail manually by using a xroad-descriptor json file as
described in chapter [X-Road Descriptor File](#x-road-descriptor-file)

If you want to generate a report for a single subsystem it is also possible to use a command line argument like this:
```bash
xroad-metrics-reports report --subsystem MYCLASS:MYMEMBER:MYSUB
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

All reports-module actions can be executed by calling the `xroad-metrics-reports` command.
Command should be executed as user `xroad-metrics` so change to that user:
```bash
sudo su xroad-metrics
```

Available actions:
```bash
xroad-metrics-reports report      # Generate reports using default arguments
xroad-metrics-reports notify      # Send pending e-mail notifications
xroad-metrics-reports --help      # Show available command line arguments
```

Above examples use the default settings file. To use another settings profile, you can use --profile flag:
```bash
xroad-metrics-reports --profile TEST report
xroad-metrics-reports --profile TEST notify
```

### Cron settings
Default installation includes a cronjob in _/etc/cron.d/xroad-metrics-reports-cron_ that runs reports-module monthly.
This job runs reports module using the default settings profile (_/etc/xroad-metrics/reports/settings.yaml_)

It is important to note that it can take several days for ==> [Collector module](collector_module.md) <== to receive
the operational data from Security Server(s) and for the ==> [Corrector_module](corrector_module.md) <== to
clean the raw data and derive monitoring metrics in a clean database collection if the X-Road instance has a lot of members.

This means that if monthly reports are to be generated, the cron job should run **after** the collector and corrector
have finished processing data for that month. By default the cron job is configured to run on 10th day of each month,
which should allow for a long enough grace period.

If you want to change the reports cronjob scheduling or settings profiles, edit the file e.g. with vi
```bash
vi /etc/cron.d/xroad-metrics-reports-cron
```
and make your changes. For example to run reports every six months on the 15th day using settings profiles `PROD` and `TEST`:
```bash
# m   h   dom  mon   dow  user             command
  1   0   15   */6    *   xroad-metrics    xroad-metrics-reports --profile TEST report
  1   3   15   */6    *   xroad-metrics    xroad-metrics-reports --profile PROD report

```

If reports-generation is to be run only manually, comment out the default cron task by adding a '#'-character:
```bash
#  1   0   10   *   *   xroad-metrics    xroad-metrics-reports report
```

### Publishing Reports
Using default settings the xroad-metrics-reports command generates report pdf files into folder _/home/xroad-metrics/reports_.
If you want to publish the reports on some external file server, you can setup e.g. a rsync cronjob.
Below example assumes your file-server hostname is _myfileserver_ and user _myuser_ can access it with from the
xroad-metrics-reports host.

If you don't use any external file server users can copy the reports to their workstations using e.g. _scp_ command.
TODO: add example

#### Set up file publishing on external file server using Nginx
```bash
sudo apt install nginx

# create /etc/nginx/sites-available/reports with content:

server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/data/reports;

        location / {
                autoindex on;
                try_files $uri $uri/ =404;  # Serve other files as well
        }

        location ~* \.pdf$ {
                types { application/pdf pdf; }  # Set the MIME type for PDF files
                default_type application/pdf;
        }
}

# enable new site:
sudo ln -s /etc/nginx/sites-available/reports /etc/nginx/sites-enabled/

# test  new configuration
sudo nginx -t

# set up relevant directories
sudo mkdir -p /var/data/reports
sudo chown -R :www-data /var/data/reports
sudo chmod -R 775 /var/data/reports
# restart Nginx
sudo systemctl restart nginx.service
```

#### Set up new user _myuser_ to sync report files on external file server

```bash
sudo adduser _myuser_
# assign new user to group www-data
sudo usermod -aG www-data _myuser_

# new user should be able access /var/data/reports and have permissions to create files there
```

#### Set up SSH authentication for _myuser_ on reports server

```bash
ssh-keygen -t rsa -b 4096 -N ""

# copy public key to external file publishing server
ssh-copy-id _myuser_@_myfileserver_

```
#### Use rsync to push report files from reports server to external file server

```bash
rsync -azP _/home/xroad-metrics/reports_/ _myuser_@_myfileserver_:/var/data/reports/
```

#### Use crontab to sync report files periodically

```bash
# create new crontab entry
crontab -e
# Sync reports every day at 5 AM.
0 5 * * * rsync -azP _/home/xroad-metrics/reports_/ _myuser_@_myfileserver_:/var/data/reports/
```


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
  log-path: /var/log/xroad-metrics/reports/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name.
The above example configuration would write logs to `/var/log/xroad-metrics/reports/logs/log_reports_EXAMPLE.json`.

Every log line includes:

- **"timestamp"**: timestamp in Unix format (epoch)
- **"local_timestamp"**: timestamp in local format '%Y-%m-%d %H:%M:%S %z'
- **"module"**: "reports"
- **"version"**: in form of "v${MINOR}.${MAJOR}"
- **"activity"**: string identifier of the logging code block
- **level**: possible values "INFO", "WARNING", "ERROR"
- **msg**: message

The **reports module** log handler is compatible with the logrotate utility. To configure log rotation for the example setup above, create the file:

```bash
sudo vi /etc/logrotate.d/xroad-metrics-reports
```

and add the following content :
```
/var/log/xroad-metrics/reports/logs/log_reports_EXAMPLE.json {
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
  heartbeat-path: /var/log/xroad-metrics/reports/heartbeat

```

The heartbeat file is written to `heartbeat-path` and heartbeat file name contains the X-Road instance name.
The above example configuration would write logs to `/var/log/xroad-metrics/reports/heartbeat/heartbeat_reports_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"
