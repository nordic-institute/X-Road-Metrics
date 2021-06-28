
# X-Road Metrics - Opendata Module

## About

The **Opendata module** is part of [X-Road Metrics](../README.md), 
which includes the following modules:
 - [Database module](../database_module.md)
 - [Collector module](../collector_module.md)
 - [Corrector module](../corrector_module.md) 
 - [Reports module](../reports_module.md) 
 - [Anonymizer module](../anonymizer_module.md)
 - [Opendata module](../opendata_module.md) 
 - [Networking/Visualizer module](../networking_module.md)

The **Opendata module** is used to publish the X-Road operational monitoring data. The module has a UI and a REST API 
that allow filtering the anonymized operational monitoring data and downloading it as gzip archives.

## Architecture

Opendata module serves data that has been prepared by the [Anonymizer module](anonymizer_module.md)  
Overview of the module architecture related to publishing operational monitoring data
through is in the diagram below:
 ![system diagram](img/opendata/opendata_overview.png "System overview")

## Networking

MongoDb is used to store "non-anonymized" operational monitoring data that should be accessible only by the X-Road administrators.
Anonymized operational monitoring data that can be published for wider audience is stored in the PostgreSQL. The opendata UI needs
access only to the PostgreSQL. To follow the "principal of least priviledge" it is recommended to
install Opendata UI on a dedicated host that has no access at all to MongoDb.

The Opendata UI is served by Apache web server using HTTPS protocol (default port 443).

## Installation

This sections describes the necessary steps to install the **opendata module** on 
an Ubuntu 20.04 Linux host. For a complete overview of different modules and machines, 
please refer to the ==> [System Architecture](system_architecture.md) <== documentation.


### Add X-Road Extensions Package Repository for Ubuntu
````bash
wget -qO - https://artifactory.niis.org/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository 'https://artifactory.niis.org/xroad-extensions-release-deb main'
````

### Install Opendata Package
To install xroad-metrics-opendata and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install xroad-metrics-opendata
```

The installation package automatically installs following items:
 * Linux users _xroad-metrics_ and _www-data_
 * xroad-metrics-opendata Django web-application package
 * Apache web server and dependencies
 * Apache configuration file template for the web-app _/etc/apache2/conf-available/xroad-metrics-opendata.conf_
 * a self signed SSL certificate
 * web-app static content under _/usr/share/xroad-metrics/opendata_
 * web-app dynamic content under _/var/lib/xroad-metrics/opendata_
 * settings file _/etc/xroad-metrics/opendata/settings.yaml_
 * log folders to _/var/log/xroad-metrics/opendata/_

Only users in _xroad-metrics_ group can access the settings files.

You have to fill in some environment specific settings to the settings file to make the Opendata module work properly.
Refer to section [Opendata Module Configuration](#opendata-module-configuration)

## Usage
### Opendata Module Configuration

To use opendata module you need to fill in your X-Road, PostgreSQL and Django configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/xroad-metrics/opendata/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* host and port of the PostgreSQL server
* username and password for opendata interface postgreSQL user
* name of PostgreSQL database where the anonymized open data is stored
* secret key for the Django web-app
* allowed hostname(s) for the web-app server

### Hostname configuration
The Apache Virtual Host configuration defines the hostname for the Opendata service.
The Opendata module installer fills in the current hostname to Apache config file automatically.

If your hostname changes, or the installer used wrong hostname, you can change the value by editing the Apache config
file `/etc/apache2/sites-available/xroad-metrics-opendata.conf`. For example if your hostname is `myhost.mydomain.org` 
change the contents of the file to:
```
Use XRoadMetricsOpendataVHost myhost.mydomain.org
```

After these changes you must restart Apache:
```bash
sudo apache2ctl restart
```

And then you can test accessing the Opendata UI by pointing your browser to `https://myhost.mydomain.org/`

The instructions above should be sufficient for simple use cases. 
For more advanced Apache configurations, e.g. to add more allowed alias names for the host, 
you need to modify the apache configuration template in `/etc/apache2/conf-available/xroad-metrics-opendata.conf`.

### Settings profiles
The opendata module can show data for multiple X-Road instances using settings profiles. 
For example to have profiles DEV, TEST and PROD create three copies of the `setting.yaml` 
file named `settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml` and 
change the xroad-instance setting in the files.

Then you can access different X-road instances data by selecting the settings profile in the url:
```
https://myhost.mydomain.org/       # settings from settings.yaml
https://myhost.mydomain.org/DEV/   # settings from settings_DEV.yaml
https://myhost.mydomain.org/TEST/  # settings from settings_TEST.yaml
https://myhost.mydomain.org/PROD/  # settings from settings_PROD.yaml
```


## Opendata Interface documentation

Opendata provides a simple GUI to query daily anonymized logs and relevant metafeatures.  
User Guide can be found from ==> [here](opendata/user_guide/ug_opendata_interface.md) <==.

Opendata provides a simple API to query daily anonymized logs and relevant metafeatures.  
Documentation can be found from ==> [here](opendata/user_guide/ug_opendata_api.md) <==.

## Monitoring and Status

### Logging 

The settings for the log file in the settings file are the following:

```yaml
xroad:
  instance: EXAMPLE

#  ...

logger:
  name: opendata
  module: opendata
  
  # Possible logging levels from least to most verbose are:
  # CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
  level: INFO

  # Logs and heartbeat files are stored under these paths.
  # Also configure external log rotation and app monitoring accordingly.
  log-path: /var/log/xroad-metrics/opendata/logs

```

The log file is written to `log-path` and log file name contains the X-Road instance name. 
The above example configuration would write logs to `/var/log/xroad-metrics/opendata/logs/log_opendata_EXAMPLE.json`.


The **opendata module** log handler is compatible with the logrotate utility. 
To configure log rotation for the example setup above, create the file:

```
sudo vi /etc/logrotate.d/xroad-metrics-opendata
```

and add the following content :
```
/var/log/xroad-metrics/opendata/logs/log_opendata_EXAMPLE.json {
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
  heartbeat-path: /var/log/xroad-metrics/opendata/heartbeat

```

The heartbeat file is written to `heartbeat-path` and hearbeat file name contains the X-Road instance name. 
The above example configuration would write logs to
 `/var/log/xroad-metrics/opendata/heartbeat/heartbeat_opendata_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"

The heartbeat is updated every time that end-users make calls to the opendata API.
If the end-user traffic is infrequent, the heartbeat can be updated manually by curling the opendata module's
heartbeat API e.g. periodically in a cronjob.

