
# X-Road Metrics - Opendata Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The **Opendata module** is part of [X-Road Metrics](../README.md),
which includes the following modules:
 - [Database module](./database_module.md)
 - [Collector module](./collector_module.md)
 - [Corrector module](./corrector_module.md)
 - [Reports module](./reports_module.md)
 - [Anonymizer module](./anonymizer_module.md)
 - [Opendata module](./opendata_module.md)
 - [Networking/Visualizer module](./networking_module.md)
 - [Opendata Collector module](./opendata_collector_module.md)

The **Opendata module** is used to publish the X-Road operational monitoring data.
The module has a UI and a REST API that allow filtering the anonymized operational monitoring data and downloading it
as gzip archives. The anonymized operational monitoring data is stored in a PostgreSQL database.

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

### Outgoing

The Opendata node needs no **outgoing** connections.

### Incoming

- The Opendata node accepts incoming connections from [Anonymizer module](anonymizer_module.md) (see also [Opendata module](opendata_module.md)).
- The Opendata node accepts incoming access from the public (preferably HTTPS / port 443, but also redirecting HTTP / port 80).

## Installation

The Opendata module installation has three main parts:
1) Install the xroad-metrics-opendata package
2) Install and configure the PostgreSQL database
3) Configure the Opendata UI

This sections describes the necessary steps to install the **opendata module** on
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


### Install the Opendata Package
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

## Database Setup
Before installing the database, please install the X-Road Metrics as described above.
After the PostgreSQL database is installed and configured you can proceed to finish configuration of the
Opendata module.

First make sure that the `en_US.UTF-8` locale is configured in the operating system:

* To set the operating system locale. Add following line to the `/etc/environment` file.

```ini
LC_ALL=en_US.UTF-8
```

* Ensure that the package `locales` is present.

```bash
sudo apt-get install locales
```

* Ensure that the locale is available.

```bash
sudo locale-gen en_US.UTF-8
```

Opendata PostgreSQL is installed from the standard Ubuntu repository:
```bash
sudo apt update
sudo apt install postgresql
```

### Automatic PostgreSQL User Creation
The X-Road Metrics Opendata package includes a command that creates the PostgreSQL users automatically.
To create PostgreSQL users for X-Road instance *LTT* run the following commands:

```bash
sudo su postgres
xroad-metrics-init-postgresql LTT
```

The command output includes a list of usernames and passwords generated:
```bash
Username       | Password     | Escaped Password
---------------+--------------+--------------------
opendata_ex    | !(p'6vR&<4!6 | "!(p'6vR&<4!6"
anonymizer_ex  | h*;74378sVk{ | "h*;74378sVk{"
networking_ex  | K!~96(;4KpB+ | "K!~96(;4KpB+"
```

Store the output to a secure location, e.g. to your password manager. These usernames and passwords are needed later
to configure the X-Road Metrics modules. The 'Escaped Password' column contains the password in YAML
escaped format that can be directly added to the config files.

Database relations and relevant indices will be created dynamically during the first run of
[Anonymizer module](anonymizer_module.md), according to the supplied configuration.

**Note:** PostgreSQL doesn't allow dashes and case sensitivity comes with a hassle.
This means that for PostgreSQL instance it is suggested to use underscores and lower characters.
The `xroad-metrics-init-postgresql` does the required substitutions in usernames automatically.


### Allowing remote access

We need to enable remote access to PostgreSQL since Anonymizer and Networking modules might reside on another server.

In this example we assume that Anonymizer host IP is 172.31.0.1 and Networking host IP is 172.31.0.2.

#### For PostgreSQL 12 on Ubuntu 20.04

Edit `/etc/postgresql/12/main/pg_hba.conf`

#### For PostgreSQL 14 on Ubuntu 22.04

Edit `/etc/postgresql/14/main/pg_hba.conf`

Add the following lines to the config in order to
enable password authentication (md5 hash comparison) from Anonymizer and Networking hosts:

```
host    opendata_ltt    anonymizer_ltt  172.31.0.1/32           md5
host    opendata_ltt    networking_ltt  172.31.0.2/32           md5
```

In the same file, remove too loose permissions by commenting out lines:

```bash
# host      all         all    0.0.0.0/0    md5
# hostssl   all         all    0.0.0.0/0    md5
```

and to reject any other IP-user-database combinations, add this to the end of the file:

```
host    all    all   0.0.0.0/0    reject
```


**Note:** `host` type access can be substituted with `hostssl` if using SSL-encrypted connections.

Then edit the `/etc/postgresql/12/main/postgresql.conf` or `/etc/postgresql/14/main/postgresql.conf` and change the *listen_addresses* to
```
listen_addresses = '*'
```

This says that PostgreSQL should listen on its defined port on all its network interfaces,
including localhost and public available interfaces.

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Establish encrypted SSL/TLS client connection

For a connection to be known SSL-secured, SSL usage must be configured on both the client and the server before the connection is made.
If it is only configured on the server, the client may end up sending sensitive information before it knows that the server requires high security.

To ensure secure connections `ssl-mode` and `ssl-root-cert` parameters has to be provided in settings file.
Possible values for `ssl-mode`: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`
For detailed information see https://www.postgresql.org/docs/current/libpq-ssl.html

To configure path to the SSL root certificate, set `ssl-root-cert`

Example of `/etc/[module]/settings.yaml` entry:
```
postgres:
  host: localhost
  port: 5432
  user: postgres
  password: *******
  database-name: opendata_LTT
  table-name: logs
  ssl-mode: verify-full
  ssl-root-cert: /etc/ssl/certs/root.crt
```

### Setting up rotational logging for PostgreSQL

PostgreSQL stores its logs by default in the directory `/var/lib/postgresql/{pg_version}/main/pg_log/` specified in `/etc/postgresql/{pg_version}/main/postgresql.conf`.

Set up daily logging and keep 7 days logs, we can make the following alterations to it:

```bash
sudo vi /etc/postgresql/12/main/postgresql.conf
```

```
logging_collector = on
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_truncate_on_rotation = on
log_rotation_age = 1d
```

It might also be relevant to log connections and modifying queries.

```bash
log_connections = on
log_disconnections = on
log_statement = 'ddl'
```

Restart PostgreSQL

```bash
sudo systemctl restart postgresql
```

If you have firewall installed, open Postgres' port 5432 for Anonymizer and Networking to connect.

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

### Apache Configuration
#### Configuration of Production Certificates
By default Networking module uses self signed SSL certificate that is created during the installation.
To replace these with proper certificates in production, you need to set your certificate file paths to
*/etc/apache2/conf-available/xroad-metrics-opendata.conf* file.

The self signed certificates and default dhparams file are installed to these paths:
- */etc/ssl/certs/xroad-metrics-dhparam.pem*
- */etc/ssl/certs/xroad-metrics-selfsigned.crt*
- */etc/ssl/private/xroad-metrics-selfsigned.key*

After configuration changes restart Apache:
```bash
sudo systemctl restart apache2.service
```

#### Hostname configuration
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

Then you can access different X-Road instances data by selecting the settings profile in the url:
```
https://myhost.mydomain.org/       # settings from settings.yaml
https://myhost.mydomain.org/DEV/   # settings from settings_DEV.yaml
https://myhost.mydomain.org/TEST/  # settings from settings_TEST.yaml
https://myhost.mydomain.org/PROD/  # settings from settings_PROD.yaml
```

### Anonymizer Module
After a fresh installation the PostgreSQL database is empty.
Setup and run [Anonymizer module](./anonymizer_module.md) to upload anonymized data into the database.

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

The heartbeat file is written to `heartbeat-path` and heartbeat file name contains the X-Road instance name.
The above example configuration would write logs to
 `/var/log/xroad-metrics/opendata/heartbeat/heartbeat_opendata_EXAMPLE.json`.

The heartbeat file consists last message of log file and status

- **status**: possible values "FAILED", "SUCCEEDED"

The heartbeat is updated every time that end-users make calls to the opendata API.
If the end-user traffic is infrequent, the heartbeat can be updated manually by curling the opendata module's
heartbeat API e.g. periodically in a cronjob.

## Metrics statistics

### Endpoint

GET  `api/statistics` will return statistical data stored in database.
