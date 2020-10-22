
| [![Republic of Estonia Information System Authority](img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Collector Module

## About

The **Collector module** is part of [X-Road v6 monitor project](../README.md), which includes modules of [Database module](database_module.md), Collector module (this document), [Corrector module](corrector_module.md), [Analysis module](analysis_module.md), [Reports module](reports_module.md), [Opendata module](opendata_module.md) and [Networking/Visualizer module](networking_module.md).

The **Collector module** is responsible to retrieve data from X-Road v6 security servers and insert into the database module. The execution of the collector module is performed automatically via a **cron job** task.

It is important to note that it can take up to 7 days for the Collector module to receive X-Road v6 operational data from (all available) security server(s).

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in one server (different users but in same group 'opmon') but also in separate servers. 

Overall system is also designed in a way, that allows to monitor data from different X-Road v6 instances (in Estonia `ee-dev`, `ee-test`, `EE`, see also [X-Road v6 environments](https://moodle.ria.ee/mod/page/view.php?id=700).

Overall system is also designed in a way, that can be used by X-Road Centre for all X-Road members as well as for Member own monitoring (includes possibilities to monitor also members data exchange partners).

## Source Code Acquisition
The module source code can be found at:

```
https://github.com/ria-ee/X-Road-opmonitor
```

and can be downloaded into server:

```bash
sudo su - collector
# If HOME not set, set it to /tmp default.
export TMP_DIR=${HOME:=/tmp}
export PROJECT="X-Road-opmonitor"
export PROJECT_URL="https://github.com/ria-ee/${PROJECT}.git"
export SOURCE="${TMP_DIR}/${PROJECT}"
if [ ! -d "${TMP_DIR}/${PROJECT}" ]; then \
    cd ${TMP_DIR}; git clone ${PROJECT_URL}; \
else \
  cd ${SOURCE}; git pull ${PROJECT_URL}; \
fi
```

## Installation

This sections describes the necessary steps to install the **collector module** in a Linux Ubuntu 18.04. To a complete overview of different modules and machines, please refer to the ==> [System Architecture](system_architecture.md) <== documentation.

## Networking

### Outgoing

- The collector module needs http-access to the X-Road CENTRALSERVER to get from global configuration list of members security servers.
- The collector module needs http-access to the current member SECURITY SERVER to get the data is collected.
- The collector module needs access to the Database Module (see ==> [Database_Module](database_module.md) <==).

### Incoming

No incoming connection is needed in the collector module.

## Install required packages

To install the necessary packages, execute the following commands:

```bash
sudo apt-get update
sudo apt-get install python3-pip
sudo pip3 install -r $SOURCE/collector_module/requirements.txt
```

## Install collector module
In the follwoing instructions it is assumed that OpMon source code is cloned into path **${SOURCE}** as instructed in [Source Code Acquisition](#Source-Code-Acquisition)

### Create users and groups
The collector module uses the system user **collector** and group **opmon**. To create them, execute:

```bash
  sudo groupadd --force opmon
  sudo groupadd --force collector
  sudo useradd --base-dir /opt --create-home --system --shell /bin/bash --gid collector collector
  sudo usermod --append --groups opmon collector
```

### Create log and heartbeat folders
Default log file path is _/var/log/opmon/collector_module_

```bash
export COLLECTOR_LOGS=/var/log/opmon/collector_module
sudo mkdir --parent $COLLECTOR_LOGS
cd $COLLECTOR_LOGS
sudo mkdir logs
sudo mkdir heartbeat
sudo chown --recursive root:opmon ./ ./logs ./heartbeat
sudo chmod --recursive g+w  ./ ./logs ./heartbeat
```

### Create settings folder
Default settings file path is _/etc/opmon/collector_module_
```bash
export COLLECTOR_SETTINGS=/etc/opmon/collector_module
sudo mkdir --parent $COLLECTOR_SETTINGS
cd $COLLECTOR_SETTINGS

sudo cp $SOURCE/collector_module/settings/ ./
sudo chown --recursive root:opmon ./
sudo chmod --recursive g+w  ./
```

To use collector you need to fill in your X-Road and MongoDB configuration into the settings file.
Refer to section [Collector Configuration](#collector-configuration)

### Install the Python package
Default Python package installation location is _/usr/local/lib/python3/site-packages/opmon/collector_module_

```bash
export COLLECTOR_PYPKG=/usr/local/lib/python3/site-packages/opmon/collector_module
sudo mkdir --parent $COLLECTOR_PYPKG
cd COLLECTOR_PYPKG
sudo cp $SOURCE/collector_module/*.py ./
sudo cp -r $SOURCE/collector_module/collectorlib ./collectorlib
sudo chown --recursive root:opmon ./
sudo chmod --recursive -x+X ./main.py
sudo chmod g+x ./main.py
sudo ln -s $(pwd)/main.py /usr/local/bin/opmon-collector
```

### Install utility scripts
Default utility script installation location is _/usr/local/opmon/collector_module/scripts_
```bash
EXPORT COLLECTOR_UTILITY=/usr/local/opmon/collector_module/scripts
sudo mkdir --parent $COLLECTOR_UTILITY
cd $COLLECTOR_UTILITY
sudo cp -r $SOURCE/collector_module/scripts ./
sudo chown --recursive collector:collector ./
sudo chmod --recursive -x+X ./
sudo find  ./ -name '*.sh' -type f | xargs chmod u+x
```

### Cleanup
Now all collector files are installed to correct paths.
The temporary source code download folder can be deleted:
```bash
rm -rf $SOURCE
```

## Usage

### Collector Configuration

To use collector you need to fill in your X-Road and MongoDB configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/opmon/collector_module/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* central- and security server hosts
* X-Road client used to collect the monitoring data
* username and password for the collector module MongoDB user

To run collector for multiple X-Road instances, a settings profile for each instance can be created. For example to have profiles DEV, TEST and PROD create three copies of `setting.yaml` 
file named `settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml`.
Then fill the profile specific settings to each file and use the --profile
flag when running opmon-collector. For example to run using the TEST profile:
```
opmon-collector --profile TEST collect
```

`opmon-collector` command searches the settings file first in current working direcrtory, then in
_/etc/opmon/collector_module/_

### Manual usage

All collector module actions can be executed by calling the `opmon-collector` command.
Command should be executed as user `collector` so change to that user:
```bash
sudo su collector
```

Some example commands:
```bash
opmon-collector list                       # Print available security servers to stdout.
opmon-collector update                     # Update security server list to MongoDB.
opmon-collector collect                    # Collect monitoring data from security server.
opmon-collector settings get mongodb.host  # Read a value from settings file and print to stdout
```

Above examples use the default settings file. To use another settings profile, you can use --profile flag:
```bash
opmon-collector --profile TEST update
opmon-collector --profile TEST collect
```

### CRON usage
A cronjob can be set up to run collector periodically.
This chapter has short instructions for setting up cronjob for a single X-Road instance.
File /usr/local/opmon/collector_module/scripts/cron/crontab contains a more complex example of cronjobs for multiple X-Road instances.


Start editing crontab for user collector:

```bash
sudo crontab -e -u collector
```

Add a  **cron job** entry that executes every 3 hours. 
Note that a different value might be needed in production.

```
0 */3 * * * /usr/local/opmon/collector_module/scripts/cron/cron_collector.sh DEV update >> /var/log/opmon/collector_module/cron_collector.log
```

To check if the collector module is properly installed for the collector user, execute:

```bash
sudo crontab -l -u collector
```

### Note about Indexing

Index build (see [Database module, Index Creation](database_module.md#index-creation) might affect availability of cursor for long-running queries.
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
  log-path: /var/log/opmon/collector_module/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/opmon/collector_module/logs/log_collector_EXAMPLE.json`.

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
sudo vi /etc/logrotate.d/collector_module
```

and add the following content :
```
/var/log/opmon/collector_module/logs/log_collector_EXAMPLE.json {
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
  heartbeat-path: /var/log/opmon/collector_module/heartbeat

```

The heartbeat file is written to `heartbeat-path` and hearbeat file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/opmon/collector_module/heartbeat/heartbeat_collector_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"

## The external files and additional scripts required for reports and networking modules

External file in subdirectory `/usr/local/opmon/collector_module/scripts/external_files/riha.json` is required for reports generation in [Reports module](reports_module.md) and networking generation on [Networking module](networking_module.md).

Generation of `riha.json` and its availability for other modules is Estonia / RIA / RIHA -specific and is not available in public.

Sample of `${APPDIR}/${INSTANCE}/collector_module/external_files/riha.json`

```json
[
  {
    "x_road_instance": "sample",
    "subsystem_name": {
      "et": "Subsystem Name ET",
      "en": "Subsystem Name EN"
    },
    "member_class": "MemberClassA",
    "email": [
      {
        "name": "Firstname Lastname",
        "email": "yourname@yourdomain"
      }
    ],
    "subsystem_code": "SubsystemCodeA",
    "member_code": "MemberCodeA",
    "member_name": "Member Name"
  }
]
```

## Appendix

NB! Mentioned appendixes below are separate products and do not log their work and do not keep heartbeat similarly as main modules.

### Collecting JSON queries and store into HDD

Collecting JSON queries and store into HDD was not part of the project scope. Nevertheless, sample scripts can be found from directory `/usr/local/opmon/collector_module/scripts/external_files`, files `collector_into_file_cron.sh`, `collector_into_file_list_servers.py` and `collector_into_file_get_opmon.py`. 

Important configuration to set up before usage:

```
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo vi ${APPDIR}/${INSTANCE}/collector_module/external_files/collector_into_file_cron.sh
```

settings:

```bash
# IP or Name of Central Server
CENTRAL_SERVER=""
```

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo vi ${APPDIR}/${INSTANCE}/collector_module/external_files/collector_into_file_get_opmon.py
```

settings:

```
# X-Road instance
INSTANCE = "sample"

# Security server IP or Name used by Central monitoring
SECURITY_SERVER = ""

# Central monitoring subsystem/member (as defined in global configuration)
#
# Message header of Instance Monitoring Client
# MEMBERCLASS is in {GOV, COM, NGO, NEE}
# Sample: MEMBERCLASS = "GOV"
MEMBERCLASS = "GOV"

# MEMBERCODE is registry code of institution
# Sample: MEMBERCODE = "70006317" # RIA, Riigi Infosüsteemi Amet, State Information Agency
MEMBERCODE = "00000001"

# SUBSYSTEMCODE is X-Road subsystem code, to be registered in RIHA, www.riha.ee
# Sample: SUBSYSTEMCODE = "monitoring"
SUBSYSTEMCODE = "Central monitoring client"
```

Usage from command line:

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
cd ${APPDIR}/${INSTANCE}/collector_module/external_files; ./collector_into_file_cron.sh
```

Usage from crontab:
```
5 */6 * * * export APPDIR="/srv/app"; export INSTANCE="sample"; cd ${APPDIR}/${INSTANCE}/collector_module/external_files; ./collector_into_file_cron.sh
```

Timestamps of last log fetched from each X-Road Member Security Server is kept in file `nextRecordsFrom.json` (hardcoded).

Log and cache files generated:

- `collector_into_file_cron.log` - general log, status 0 (success) or 1 (failure)
- `SERVERS_CACHE_NOW` = "${CACHE_DIR}/cache_${CENTRAL_SERVER}_${NOW}.${CACHE_EXT}"
- `SERVERS_CACHE` = "${CACHE_DIR}/cache_${CENTRAL_SERVER}.${CACHE_EXT}" as symbolic link to last $SERVERS_CACHE_NOW}
- `LOG_FILE` = "log_${CENTRAL_SERVER}_${NOW}.${LOG_EXT}"


### Collecting JSON queries from HDD

It is possible to read JSON queries from HDD files produced by `collector_into_file_cron` and send thenm to MongoDB using the command script `collector_from_file`:

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
#     # Get arguments
#     parser = argparse.ArgumentParser()
#     parser.add_argument('MONGODB_DATABASE', metavar="MONGODB_DATABASE", type=str, help="MongoDB Database")
#     parser.add_argument('MONGODB_USER', metavar="MONGODB_USER", type=str, help="MongoDB Database SUFFIX")
#     parser.add_argument("FILE_PATTERN", help="FILE_PATTERN: string with file name or file pattern")
#     parser.add_argument('--password', dest='mdb_pwd', help='MongoDB Password', default=None)
#     parser.add_argument('--auth', dest='auth_db', help='Authorization Database', default='auth_db')
#     parser.add_argument('--host', dest='mdb_host', help='MongoDB host (default: %(default)s)',
#                         default='127.0.0.1:27017')
#     parser.add_argument('--confirm', dest='confirmation', help='Skip confirmation step, if True', default="False")
#
# Path to the logs. Leave empty for current directory
# NB! Number of log lines in each file "${LOG_PATH}/${INSTANCE}.*.*.log*" is suggested to be limited with 
#   100 000 lines per 1Gb RAM available
export LOG_PATH="./${INSTANCE}/`date '+%Y/%m/%d'`"
export MONGODB_SERVER=`grep "^MONGODB_SERVER = " ${APPDIR}/${INSTANCE}/collector_module/settings.py | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g"`
# Please note, that PASSWORD is now available in user settings during current session and 
# will be also available in ~/.bash_history. To avoid that, we do not suggest such usage
export PASSWORD=`grep "^MONGODB_PWD = " ${APPDIR}/${INSTANCE}/collector_module/settings.py | cut -d'=' -f2 | sed -e "s/ //g" | sed -e "s/\"//g"`
#
for file in `ls ${LOG_PATH}/${INSTANCE}.*.*.log*` ; do \
    sudo --user collector /usr/bin/python3 ${APPDIR}/${INSTANCE}/collector_module/external_files/collector_from_file.py \
	query_db_${INSTANCE} collector_${INSTANCE} $file \
	--password ${PASSWORD} --auth auth_db --host ${MONGODB_SERVER}:27017 --confirm True ; done
```
