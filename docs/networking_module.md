
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Networking / Visualizer Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The Networking module is part of [X-Road Metrics](../README.md). All other modules in X-Road Operational Monitoring are:
 - [Database module](./database_module.md)
 - [Collector module](./collector_module.md)
 - [Corrector module](./corrector_module.md)
 - [Reports module](./reports_module.md)
 - [Anonymizer module](./anonymizer_module.md)
 - [Opendata module](./opendata_module.md)
 - [Networking/Visualizer module](./networking_module.md)
 - [Opendata Collector module](./opendata_collector_module.md)

The purpose of the **Networking module** is to visualize the networking activity between the X-Road members.
It consists of:

1. **Data preparation** R script that queries the Open data PostgreSQL database,
does relevant calculations (query counts between X-Road members) and writes a table file to be used in the
visualization web application;

1. RStudio Shiny-based **web application** to visualize the networking activity between the X-Road members.

Both components are scripted in the [R language] (https://www.r-project.org/about.html).

## Processes flow chart

The general scheme of processes in the Networkin module is as follows:

![networking module diagram](img/Networking_module_diagram.png "Networking module diagram")

### Add X-Road Extensions Package Repository for Ubuntu 20.04 or Ubuntu 22.04
````bash
wget -qO - https://artifactory.niis.org/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository 'https://artifactory.niis.org/xroad-extensions-release-deb main'
````

The following information can be used to verify the key:
- key hash: 935CC5E7FA5397B171749F80D6E3973B
- key fingerprint: A01B FE41 B9D8 EAF4 872F A3F1 FB0D 532C 10F6 EC5B
- 3rd party key server: [Ubuntu key server](https://keyserver.ubuntu.com/pks/lookup?search=0xfb0d532c10f6ec5b&fingerprint=on&op=index)

### Install xroad-metrics-networking package
When the repository is added to Ubuntu you can install xroad-metrics-networking module package by running these commands:
```bash
sudo apt update
sudo apt install xroad-metrics-networking
```

The package installs the following components:
- Linux user and group xroad-metrics that has the privileges to run the xroad-metrics programs
- xroad-metrics-networking command that runs the data preparation script
- static data files and helper scripts under /usr/share/xroad-metrics/networking
- settings files under /etc/xroad-metrics/networking
- cron configuration to run the data preparation periodically in /etc/cron.d/xroad-metrics-networking-cron
- shiny web app files under /usr/share/xroad-metrics/networking/shiny
- Shiny Server configuration file /etc/shiny-server/shiny-server.conf
- Apache web server and dependencies
- Apache configuration file for the web-app _/etc/apache2/conf-available/xroad-metrics-analyzer-ui.conf_
- a self signed SSL certificate

Note that the package does not install Shiny Server itself. See next chapter for further instructions.
Apache is used as a reverse proxy in front of Shiny Server to add SSL encryption.

### Install Shiny Server
Shiny Server is an open source, free of charge webserver that serves web-apps written using the R-language Shiny
framework. The Networking module UI is a Shiny app and requires Shiny Server to run.
Shiny Server is developed and distributed by RStudio (https://rstudio.com/products/shiny/shiny-server/),
and currently they don't provide an Ubuntu repository for it. Therefore, Shiny Server is not included as a dependency
of the xroad-metrics-networking package installed above.

However,the xroad-metrics-networking package includes a utility script that can be used to download and install Shiny Server
from the RStudio website. To install Shiny Server via this utility script, run:
```bash
sudo /usr/share/xroad-metrics/networking/install-shiny-server.sh
```

A default configuration file for Shiny Server is included in xroad-metrics-networking package and Shiny Server will
use it automatically.

## Configuration
### Default settings file
Default settings file for xroad-metrics-networking data preparation step is /etc/xroad-metrics/networking/settings.yaml

Before running the data preparation, user should fill in the following configuration:
  - X-Road instance name
  - Open data PostgreSQL database connection configuration

Additionally, the following parameters can be adjusted in the settings file:
  - Time interval for data to be fetched from Open data PostgreSQL database
  - List of metaservices
  - Logging configuration
  - Subsystem-info file location

### Subsystem-info file
During the data preparation step networking module adds subsystem names to the data.
Subsystem names are fetched from a json file that holds the subsystem info.
Default location for this file is /etc/xroad-metrics/networking/riha.json

TODO: solve riha.json handling: OPMONDEV-90, OPMONDEV-91

### Settings profiles
The xroad-metrics-networking module supports displaying data for multiple X-Road instances via settings profiles.
For example to have profiles DEV, TEST and PROD create three copies of `setting.yaml`
file named `settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml`.
Then fill the profile specific settings to each file and use the --profile
flag when running xroad-metrics-networking command. For example to run using the TEST profile:
```
xroad-metrics-networking --profile TEST
```

In order for the periodic cron job to be ran under a specific profile, the command inside
`/etc/cron.d/xroad-metrics-networking-cron` should also be updated. For example to run the job under the TEST profile,
the command should be represented in the following way:
```
/usr/share/xroad-metrics/networking/networking-cron-entrypoint.sh TEST
```

Now the xroad-metrics-networking data preparation program will get configuration settings from a settings file named
settings_TEST.yaml. The command searches the settings file first in current working direcrtory,
then in _/etc/xroad-metrics/networking/_. xroad-metrics-networking command will then tag the generated output files with the profile
name (TEST in this case).

In the UI you can view the data of different settings profiles by providing the *profile* query parameter.
E.g. if the Shiny Server is running on host *myshiny* and port 3838 then you can view the data prepared using settings
profile TEST by browsing to http://myshiny:3838?profile=TEST

### Database (PostgreSQL) setup

See [Opendata database](opendata_module.md)

#### Establish encrypted SSL/TLS client connection

For a connection to be known SSL-secured, SSL usage must be configured on both the client and the server before the connection is made.
If it is only configured on the server, the client may end up sending sensitive information before it knows that the server requires high security.

To ensure secure connections `ssl_mode` and `ssl_root_cert` parameterers has to be provided in settings file.
Possible values for `ssl_mode`: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`
For detailed information see https://www.postgresql.org/docs/current/libpq-ssl.html

To configure path to the SSL root certificate, set `ssl_root_cert`

Example of `/etc/settings.yaml` entry:
```
postgres:
  host: localhost
  port: 5432
  user: postgres
  password: *******
  ssl_mode: verify-ca
  ssl_root_cert: /etc/ssl/certs/root.crt
```

### Apache Configuration
#### Configuration of Production Certificates
By default Networking module uses self signed SSL certificate that is created during the installation.
To replace these with proper certificates in production, you need to set your certificate file paths to
*/etc/apache2/conf-available/xroad-metrics-networking.conf* file.

The self signed certificates and default dhparams file are installed to these paths:
- */etc/ssl/certs/xroad-metrics-dhparam.pem*
- */etc/ssl/certs/xroad-metrics-selfsigned.crt*
- */etc/ssl/private/xroad-metrics-selfsigned.key*

After configuration changes restart Apache:
```bash
sudo systemctl restart apache2.service
```

#### Networking Module and Opendata Module on Same Host
It is possible to install Networking module and Opendata module on same host. This configuration
is not recommended for production use but can be used e.g. when testing X-Road Metrics.
If Networking and Opendata modules are on the same host, Apache configuration needs to be adjusted to
route traffic to each service. Simplest way is to set up two DNS names for the host and set configure
one Apache virtual host for each module.

So assume that the host has two DNS names: *xroad-metrics-networking.mydomain.org* and
*xroad-metrics-opendata.mydomain.org* then you can simply change check that the domain names
are set in Apache site configurations.

For Networking module edit file */etc/apache2/sites-available/xroad-metrics-networking.conf* and
set contents to
```
Use XroadMetricsNetworkingVHost xroad-metrics-networking.mydomain.org
```

For Opendata module edit file */etc/apache2/sites-available/xroad-metrics-opendata.conf* and
set contents to
```
Use XroadMetricsOpendataVHost xroad-metrics-opendata.mydomain.org
```

After configuration changes restart Apache:
```bash
sudo systemctl restart apache2.service
```

## Data preparation script, overview

The data preparation step can be started by the command `xroad-metrics-networking`. It does the following:

1. Read configuration parameters from a settings-file. Default settings-file is `/etc/xroad-metrics/networking/settings.yaml`.
2. Read instance specific complementary files `/etc/xroad-metrics/networking/riha.json`
   in order to link `clientmembercode` and `servicemembercode` to the names of the X-Road members.
3. Establishes a connection to Open data PostgreSQL and queries the most recent date in field `requestindate`.
4. Queries the most recent data from Open data dating back to certain number of days
   ('interval' in settings file, default 30 days) from the most recent `requestindate`.
   The script retrieves only `succeeded=True` logs. The script retrieves the following fields:

    ```
    requestindate, clientmembercode, clientsubsystemcode,
    servicemembercode, servicesubsystemcode, servicecode
    ```

5. Calculates the count of service calls between each unique combination of the fields:

    ```
    clientmembercode, clientsubsystemcode, servicemembercode,
    servicesubsystemcode, servicecode
    ```

6. Adds the following concatenate fields `client`, `producer`, `producer.service`
   using newline escape sequence as a separator:

    ```
    client=paste(clientmembercode, clientsubsystemcode, sep='\n')
    producer=paste(servicemembercode, servicesubsystemcode, sep='\n')
    producer.service=paste(servicemembercode, servicesubsystemcode, servicecode, sep='\n')
    ```

7. Parses member names from `riha.json` and adds the names to the output data.
8. Writes the resulting table to RDS-file (R-specific binary file)
   in the shiny application's dynamic data directory (`/var/lib/xroad-metrics/networking`)

The `xroad-metrics-networking` data preparation command is set up to run periodically using cron.

## Visualization web application

After the xroad-metrics-networking package and Shiny Server are installed and the data-preparation has been executed for the
first time, the Visualization Web App UI can be accessed using a browser.

By default the Shiny Server is configured to run on port 3838, so if the host where xroad-metrics-networking and Shiny Server
are installed is named e.g. *myshiny* you can access the UI by pointing your browser to http://myshiny:3838.

The visualization web application enables the end-user to get visually illustrated information on the networking
activity between the X-Road members. User can:

1. Select to visualize all members or select one member.
2. Select a "Top n" threshold to show only service calls reaching the highest n count of queries.
3. Select the level of details with three options: member level, subsystem level, service level.
4. Select whether the X-Road members are displayed as their registry codes or names.
5. Select whether to include metaservices
   (services related to the X-Road monitoring and service discovery).

The visualization output includes two different graphs:

1. The upper network graph shows members as circular nodes and arrows between the nodes to signify
   the connections between the members. Stronger color and thicker line indicates higher number of queries.
   The arrow points in a direction of client --> producer.
2. The lower heatmap-type graph shows the same information but in a different form.
   The members in a producer role are plotted on the horizontal axis while the members in a client role are plotted
   on the vertical axis. The intersections (colored cells) of members on the horizontal and vertical axes indicate
   the number of queries between the given X-Road members. Greener colors signify lower number of queries and red
   colors higher number of colors.

The numbers of queries between the members are logarithmed (log10) in both graphs in order to enable color and
line thickness graduations.

The back-end of the web application a Shiny-framework web-app installed into `/usrr/share/xroad-metrics/networking/shiny/app.R`.
In addition to setting up the user interface, the script also does service call counting and logarithming.
The data file prepared by `prepare_data.R` includes counts of service calls on the service level.
For displaying X-Road member networking on the higher levels (member, subsystem), the `app.R` script reactively
sums the query counts.


## Logging

### Data preparation script

The log files are stored by default at `/var/log/xroad-metrics/networking/logs`.
The local timestamp (YYYY-MM-DD hh:mm:ss), Unix timestamp, duration (hh:mm:ss), log information level (INFO, ERROR),
activity and message are recorded in JSON structure:

```
{
  "module":"networking_module",
  "local_timestamp":"2017-11-16 20:32:16",
  "timestamp":1510857136, "duration":"00:00:01",
  "level":"INFO",
  "activity":"data preparation ended",
  "msg":"1 rows were written for visualizer."
}
```

Heartbeat info is stored by default at `/var/log/xroad-metrics/networking/heartbeat`.
Heartbeat has two statuses: SUCCEEDED and FAILED

```
{
  "module":"networking_module",
  "local_timestamp":"2017-11-16 20:32:16",
  "timestamp":1510857136,
  "msg":"SUCCEEDED"
}
```

### Shiny Server

Rstudio Shiny Server Open Source has its own built-in logging.
All information related to Shiny Server itself, rather than a particular Shiny application,
is logged in the global system log stored in `/var/log/shiny-server.log`.
Any errors and warnings that Shiny Server needs to communicate will be written here.
The application-specific logs, in this case the applications residing in `/usr/share/xroad-metrics/networking/shiny` subfolders,
are logged separately and stored in `/var/log/shiny-server`. The log files are created in the following format:
`<application directory name>-YYYMMDD-HHmmss-<port number or socket ID>.log`, e.g. `sample-shiny-20171021-232458-41093.log`.

A log file will be created for each R process when it is started. However, if a process closes successfully,
the error log associated with that process will be automatically deleted.
The only error log files that will remain on disk are those associated with R processes that did not exit as expected.
For more information on the Shiny Server server level logging,
please see the [Server Log section of Shiny Server manual](http://docs.rstudio.com/shiny-server/#server-log).

For more information on the Shiny Server application level logging, please see the
[Logging and Analytics section of Shiny Server manual](http://docs.rstudio.com/shiny-server/#logging-and-analytics).

## Link Shiny Server application with Google Analytics ID

Google Analytics ID can be added to Shiny web applications in Shiny Server configuration file
`/etc/shiny-server/shiny-server.conf`.
The following row must be added to the relevant application folder location
`google_analytics_id "UA-12345-1"` (ID to be replaced by a correct one).

Restart Shiny Server service after changes:

```bash
sudo service shiny-server restart
```

For more information on how to use Google Analytics, including the method of how to set different Google Analytics IDs
to different applications, please see the
[3.5.3 Google Analytics section of Shiny Server manual](http://docs.rstudio.com/shiny-server/#google-analytics).


## Possible optimization ideas

At of the current implementation, `prepare_data.R` queries data from Opendata PostgreSQL database time interval in 30 days (configurable `interval=30` in `${APPDIR}/${INSTANCE}/networking_module/prepare_data_settings.R` and prepares everything based of that.
This might be memory-consuming.
Basically, there are next options to optimize usage of RAM:

1. reduce interval
2. implement logic to fetch data only in one day interval and append it into `/srv/shiny-server/${INSTANCE}/dat.rds`
3. use R garbage collection utility gc() within `prepare_data.R`
