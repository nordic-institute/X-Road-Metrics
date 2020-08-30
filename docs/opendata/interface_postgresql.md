
| [![Republic of Estonia Information System Authority](../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Open Data Module, Interface and PostgreSQL Node

## About

Opendata module is part of [X-Road v6 monitor project](../../README.md), which includes modules of [Database module](../database_module.md), [Collector module](../collector_module.md), [Corrector module](../corrector_module.md), [Analysis module](../analysis_module.md), [Reports module](../reports_module.md), Opendata module (this document) and [Networking/Visualizer module](../networking_module.md).

**Interface** is an API and a GUI to access the already anonymized data by [Anonymizer Node](anonymizer.md).

The module source code can be found at:

```
https://github.com/ria-ee/X-Road-opmonitor
```

and can be downloaded into server:

```bash
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

## Networking

### Outgoing

No **outgoing** connection is needed in the interface module.

### Incoming

- The Interface and PostgreSQL node accepts incoming connections from [Anonymizer module](anonymizer.md) (see also [Opendata module](../opendata_module.md)).
- The Interface and PostgreSQL node accepts incoming access from the public (preferably HTTPS / port 443, but also redirecting HTTP / port 80).
- The Interface and PostgreSQL node is protected by Estonian ID-card authentication, but no specific roles or user rights during pilot stage.

## Installation

Interface and PostgreSQL node has 3 main components:

1. PostgreSQL;
2. Apache;
3. Open Data Django application.

Contents of this installation guide:

1. [Set up PostgreSQL to store anonymized data](#1-postgresql);
2. [Install Apache, which will serve Open Data Django applications](#2-apache);
3. [Set up Open Data for different X-Road instances](#3-django-web-applications);
4. [Configure Apache to serve Open Data Django application](#4-configuring-apache)

## 1. PostgreSQL

### Setting up the database

Opendata module uses [PostgreSQL](https://www.postgresql.org/ "PostgreSQL") to store the anonymized data ready for public use.
Current instructions are for PostgreSQL 9.5.

A database with remote connection capabilities must be set up beforehand. 
Relations and relevant indices will be created dyncamically during the first run of [Anonymizer module](anonymizer.md), according to the supplied configuration.

### Downloading PostgreSQL 9.5

Ubuntu 16.04.3 has PostgreSQL 9.5 in its default *apt* repository.

```bash
sudo apt-get --yes update 
sudo apt-get install postgresql
```

### Creating users and databases

Switch to *postgres* user to create a database and corresponding PostgreSQL users.

```bash
sudo su --login postgres
```

Enter PostgreSQL interactive terminal.

```bash
psql
```

#### Integration test

If running integration tests for Open Data, the following PostgreSQL user and database must be set up:

```
postgres=# CREATE USER ci_test WITH PASSWORD 'ci_test';
postgres=# CREATE DATABASE opendata_ci_test WITH TEMPLATE template1 
postgres-#     ENCODING 'utf8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8';
postgres=# GRANT CREATE, CONNECT ON DATABASE opendata_ci_test TO ci_test
postgres-#     WITH GRANT OPTION;
postgres=# \q
```

#### X-Road instances

Create *anonymizer* and *opendata* PostgreSQL users, *opendata* database and grant the privileges.

**Note:** database name must match respective X-Road instance Anonymizer's and Django application's
`mongodb['database_name']`. Same goes for user and `mongodb['user']`.

In this manual, `sample` is used as INSTANCE. 
To repeat for another instance, please change `sample` to map your desired instance.

**Note:** PostgreSQL doesn't allow dashes and case sensitivity comes with a hassle.
This means that for PostgreSQL instance it is suggested to use underscores and lower characters (usage: .format(X_ROAD_INSTANCE.lower().replace('-', '_')).

In Estonia, X-Road instances `ee-dev`, `ee-test` and `EE` are in use. Therefor, following substitutions have to be made:
```
ee-dev -> ee_dev
ee-test -> ee_test
EE -> ee
```

Replace **${PWD_for_...}** with the desired password.

**Note:** Selected passwords must also be adjusted in Anonymizer module and Interface module settings.

**Note:** We don't create tables nor do we grant table privileges to *interface* and *networking* users, as
*anonymizer* creates the tables and grants read-only access to those parties in the run time.
```
postgres=# CREATE USER anonymizer_sample WITH PASSWORD '${PWD_for_anonymizer_sample}';
postgres=# CREATE USER interface_sample WITH PASSWORD '${PWD_for interface_sample}';
postgres=# CREATE USER networking_sample WITH PASSWORD '${PWD_for networking_sample}';
postgres=# CREATE DATABASE opendata_sample WITH TEMPLATE template1 
postgres-#     ENCODING 'utf8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8';
postgres=# GRANT CREATE, CONNECT ON DATABASE opendata_sample TO anonymizer_sample
postgres-#     WITH GRANT OPTION;
postgres=# GRANT CONNECT ON DATABASE opendata_sample TO interface_sample;
postgres=# GRANT CONNECT ON DATABASE opendata_sample TO networking_sample;
postgres=# \q
```

Log out from *postgres* user.

```bash
logout
```

### Allowing remote access

PostgreSQL needs remote access, since Anonymizer resides on another machine.

To allow remote access to PostgreSQL, add the following lines to `/etc/postgresql/9.5/main/pg_hba.conf` in order to
enable password authentication (md5 hash comparison) from Anonymizer node and only localhost access for Interface.

In this manual, `sample` is used as INSTANCE. 
To repeat for another instance, please change `sample` to map your desired instance.

**Note:** `host` type access can be substituted with `hostssl` if using SSL-encrypted connections.

```bash
sudo cp --preserve /etc/postgresql/9.5/main/pg_hba.conf{,.bak}

# Set ${ANONYMIZER_IP}
export ANONYMIZER_IP=`dig +short opmon-anonymizer`
export NETWORKING_IP=`dig +short opmon-networking`
export PG_INSTANCE="sample"

echo "host     opendata_${PG_INSTANCE}   anonymizer_${PG_INSTANCE}   ${ANONYMIZER_IP}/32   md5" | \
    sudo tee --append /etc/postgresql/9.5/main/pg_hba.conf
echo "host    opendata_${PG_INSTANCE}    interface_${PG_INSTANCE}    127.0.0.1/32    md5" | \
    sudo tee --append /etc/postgresql/9.5/main/pg_hba.conf
 echo "host    opendata_${PG_INSTANCE}    networking_${PG_INSTANCE}    ${NETWORKING_IP}/32    md5" | \
    sudo tee --append /etc/postgresql/9.5/main/pg_hba.conf
```

Remove too loose permissions:

```bash
sudo vi /etc/postgresql/9.5/main/pg_hba.conf
```

by commenting out lines:

```bash
# host      all         all    0.0.0.0/0    md5
# hostssl   all         all    0.0.0.0/0    md5
```

To reject any other IP-user-database combinations, execute:

```bash
echo "host    all    all   0.0.0.0/0    reject" | \
    sudo tee --append /etc/postgresql/9.5/main/pg_hba.conf
```

Allow remote clients by changing or adding into

```bash
sudo vi /etc/postgresql/9.5/main/postgresql.conf
```

the following line:

```
listen_addresses = '*'
```

This says that PostgreSQL should listen on its defined port on all its network interfaces, including localhost and public available interfaces.

### Setting up rotational logging

PostgreSQL stores its logs by default in the directory `/var/lib/postgresql/9.5/main/pg_log/` specified in `/etc/postgresql/9.5/main/postgresql.conf`. 

Set up daily logging and keep 7 days logs, we can make the following alterations to it:

```bash
sudo vi /etc/postgresql/9.5/main/postgresql.conf
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
sudo service postgresql restart
```

If you have firewall installed, open Postgres' port 5432 for Anonymizer to connect.

**WARNING:** **Although ufw is convenient, enabling it overrules/wipes the iptables, INCLUDING ACCESS TO 22 FOR SSH. 
Always allow 22 after enabling.** 

```bash
sudo apt-get install --yes ufw
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 5432/tcp
```

To verify that the ports are open, run

```bash
sudo ufw status
```

This should output something similar to

```
Status: active

To                         Action      From
--                         ------      ----
22                         ALLOW       Anywhere                  
5432/tcp                   ALLOW       Anywhere                  
22 (v6)                    ALLOW       Anywhere (v6)             
5432/tcp (v6)              ALLOW       Anywhere (v6)
```

## 2. Apache

Install Apache and relevant libraries in order to be able to serve Interface instances.

```bash
sudo apt-get --yes update
sudo apt-get install --yes apache2 apache2-utils libexpat1 ssl-cert apache2-dev
```

**Note:** Apache installation creates user **www-data**. Django application, which serves Open Data Interface, is run with its _www-data_ permissions.

Open both ports 443 (HTTPS) and 80 (HTTP) for Apache. Enabling `ufw` and port 22 (ssh) in case PostgreSQL section isn't completed.

**WARNING:** **Although ufw is convenient, enabling it overrules/wipes the iptables, INCLUDING ACCESS TO 22 FOR SSH. 
Always allow 22 after enabling.** 

```bash
sudo apt-get install ufw
sudo ufw enable
sudo ufw allow 22
sudo ufw allow https
sudo ufw allow http
```

To verify that the ports are open, run

```bash
sudo ufw status
```

This should output something similar to

```
Status: active

To                         Action      From
--                         ------      ----
22                         ALLOW       Anywhere
80                         ALLOW       Anywhere
443                        ALLOW       Anywhere
22 (v6)                    ALLOW       Anywhere (v6)
80 (v6)                    ALLOW       Anywhere (v6)
443 (v6)                   ALLOW       Anywhere (v6)
```

To test whether Apache works, the next command should output a web page source:

```bash
sudo apt-get install --assume-yes curl
curl localhost
```

## 3. Django web applications

The Interface module uses the system user **www-data** (Apache) and group **opmon**. To create them, execute:

```bash
sudo groupadd --force opmon
sudo usermod --append --groups opmon www-data
```

### Create relevant X-Road instances

Each X-Road instance needs its own instance of Interface.

In this manual, `sample` is used as INSTANCE. 
To repeat for another instance, please change `sample` to map your desired instance.

```bash
export APPDIR="/srv/app"
export WEBDIR="/var/www"
export INSTANCE="sample"
```
Web server content is stored in `${WEBDIR}`,  logs and heartbeats in `${APPDIR}`.

```bash
# export APPDIR="/srv/app"; export WEBDIR="/var/www"; export INSTANCE="sample"
sudo mkdir --parents ${WEBDIR}/${INSTANCE}/opendata_module

# Copy the code from repository to the default Apache directory
sudo cp --recursive --preserve \
    ${SOURCE}/opendata_module/interface \
    ${WEBDIR}/${INSTANCE}/opendata_module

# Create log and heartbeat directories with group 'opmon' write permission
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo mkdir --parents ${APPDIR}/${INSTANCE}
sudo mkdir --parents ${APPDIR}/${INSTANCE}/logs
sudo mkdir --parents ${APPDIR}/${INSTANCE}/heartbeat
sudo chown root:opmon ${APPDIR}/${INSTANCE} ${APPDIR}/${INSTANCE}/logs ${APPDIR}/${INSTANCE}/heartbeat
sudo chmod g+w ${APPDIR}/${INSTANCE} ${APPDIR}/${INSTANCE}/logs ${APPDIR}/${INSTANCE}/heartbeat

# Database directory to store Django's internal SQLite database.
# sudo mkdir --parents ${WEBDIR}
# sudo mkdir --parents ${WEBDIR}/${INSTANCE}
# sudo mkdir --parents ${WEBDIR}/${INSTANCE}/opendata_module
# sudo mkdir --parents ${WEBDIR}/${INSTANCE}/opendata_module/interface
sudo mkdir --parents ${WEBDIR}/${INSTANCE}/opendata_module/interface/database
sudo chown www-data:www-data ${WEBDIR}/${INSTANCE}/opendata_module/interface/database
```

Settings for different X-Road instances have been prepared and can be used:

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo rm -f ${WEBDIR}/${INSTANCE}/opendata_module/interface/interface/settings.py
sudo ln --symbolic \
    ${WEBDIR}/${INSTANCE}/opendata_module/interface/instance_configurations/settings_${INSTANCE}.py \
    ${WEBDIR}/${INSTANCE}/opendata_module/interface/interface/settings.py
```

If needed, edit necessary modifications to the settings file using your favorite text editor (here, **vi** is used):

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo vi ${WEBDIR}/${INSTANCE}/opendata_module/interface/interface/settings.py
```

These are the settings that **must** be definitely set:

```python
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = ['opmon-opendata', 'localhost', '127.0.0.1']
X_ROAD_INSTANCE = 'sample'
```

```python
POSTGRES_CONFIG = {
    'host_address': '127.0.0.1',
    'port': 5432,
    'database_name': 'opendata_sample',
    'table_name': 'logs',
    'user': 'interface_sample',
    'password': '${PWD_for_interface_sample}'
}
```

These are the settings that will work with default values set but can be changed while needed:

```python
LOGS_DIR = '/srv/app/{0}/logs/'.format(X_ROAD_INSTANCE)
DISCLAIMER = """ """
HEADER = """ """
FOOTER = """ """
PREVIEW_LIMIT = 100
HEARTBEAT_DIR = '/srv/app/{0}/heartbeat/'.format(X_ROAD_INSTANCE)
```

Correct necessary permissions

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo chown --recursive www-data:www-data ${WEBDIR}/${INSTANCE}/opendata_module
sudo chmod --recursive -x+X ${WEBDIR}/${INSTANCE}/opendata_module
```

### Installing Python libraries

Interface has been written with Python 3.5.2 in mind, which is the default preinstalled _python3_ version for Ubuntu 16.04.3 LTS.

Most libraries follow the "MAJOR.MINOR.PATCH" schema, so the guideline is to review and update PATCH versions always (they mostly contain bug fixes). MINOR updates can be applied,  as they should keep compatibility, but there is no guarantee for some libraries. A suggestion would be to check if tests are working after MINOR updates and rollback if they stop working. MAJOR updates should not be applied.

Get _pip3_ tool for downloading 3rd party Python libraries for _python3_ along with system dependencies.

```bash
sudo apt-get --yes upgrade
sudo apt-get --yes install python3-pip libpq-dev libyaml-dev
sudo pip3 install -r ${SOURCE}/opendata_module/interface/requirements.txt
```

We also need our Python version specific *mod_wsgi* build to serve Python applications through WSGI and Apache.

```bash
sudo pip3 install mod_wsgi
```

This builds us a *mod_wsgi* for our *python3* version. We will install and load it when we configure Apache.

### Setting up Django SQLite databases for Interface

Interface (API and GUI) runs on Django.

In order for Django application to work, the internal SQLite database must be set up. For that, run:

```bash
# Create schemas and then create corresponding tables
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo --user www-data python3 ${WEBDIR}/${INSTANCE}/opendata_module/interface/manage.py makemigrations
sudo --user www-data python3 ${WEBDIR}/${INSTANCE}/opendata_module/interface/manage.py migrate
```

### Collecting static files for Apache

Static files are scattered during the development in Django. 
To allow Apache to serve the static files from one location, they have to be collected (copied to a single directory). 
Collect static files for relevant instances to `${WEBDIR}/${INSTANCE}/opendata_module/interface/static` by default (`STATIC_ROOT` value in `settings.py`):

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo python3 ${WEBDIR}/${INSTANCE}/opendata_module/interface/manage.py collectstatic <<<yes
```

Make the _root:root_ static directory explicitly read-only for others (including _www-data_):

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo chown --recursive root:root ${WEBDIR}/${INSTANCE}/opendata_module/interface/static
sudo chmod --recursive o-w ${WEBDIR}/${INSTANCE}/opendata_module/interface/static
sudo chmod --recursive g-w ${WEBDIR}/${INSTANCE}/opendata_module/interface/static
```

## 4. Configuring Apache

Let Apache know of the correct WSGI instance by replacing Apache's default mod_wsgi loader.

```bash
sudo cp --preserve /etc/apache2/mods-available/wsgi.load{,.bak}
sudo mod_wsgi-express install-module | head --lines 1 | sudo tee /etc/apache2/mods-available/wsgi.load
```

Create an Apache configuration file at **/etc/apache2/sites-available/opendata.conf** for port 80 (http). 

**Note:** To configure port 443 (https), public domain address and certificates are required.

**Note:** The correct Python interpreter is derived from the loaded *wsgi_module*.

```bash
sudo vi /etc/apache2/sites-available/opendata.conf
```

**Note:** `hostname -I` is probably the easiest way to get machine's IP address for `<machine IP>`. `<machine IP>` can be substituted with public domain name, once it's acquired.

```
<VirtualHost <machine IP>:80>
        ServerName <machine IP>
        ServerAdmin yourname@yourdomain

        ErrorLog ${APACHE_LOG_DIR}/opendata-error.log
        CustomLog ${APACHE_LOG_DIR}/opendata-access.log combined

        WSGIApplicationGroup %{GLOBAL}

        #### Open Data instances ####
        #### Use one or more instances here if needed ####

        ## SAMPLE ##

        WSGIDaemonProcess sample
        WSGIScriptAlias /sample /var/www/sample/opendata_module/interface/interface/wsgi.py process-group=sample

        # Suffices to share static files only from one X-Road instance, as instances share the static files.
        Alias /static /var/www/sample/opendata_module/interface/static

        <Directory /var/www/sample/opendata_module/interface/static>
                Require all granted
        </Directory>

</VirtualHost>
```

After we have defined our *VirtualHost* configuration, we must enable the new *site* --- *opendata.conf* --- so that
Apache could start serving it.

```bash
sudo a2ensite opendata.conf
sudo a2enmod wsgi
```

Finally, we need to reload Apache in order for the site update to apply.

```bash
sudo service apache2 reload
```

## Accessing Opendata interface

Navigate to https://opmon-opendata/sample/gui (or http when no security certificate in place yet)
(to repeat for another instance, please change `sample` to map your desired instance).

## Testing installation

To verify that the Open Data Interface is set up correctly and the underlying PostgreSQL database is reachable, make the temporary configuration changes and run the scripts as stated ==> [HERE, **Open Data Interface Test**](../tests/tests_opendata_interface.md) <==. 

## Extra security measures

### Enforcing security upon users

### Limit ssh connections to internal network

```bash
sudo ufw allow from 10.0.24.42/24 to any port 22
``` 

### Allow only SSH key based login

```bash
sudo cp --preserve /etc/ssh/sshd_config{,.bak}
sudo vi /etc/ssh/sshd_config
```

Disable the following features:

```
PasswordAuthentication no
ChallengeResponseAuthentication no
```

Restart SSH service:

```bash
service ssh restart
```

## Scaling

* **Interface**
	Upscaling (more services): more RAM to handle larger log files.
	Upscaling (more end users): more CPUs and RAM for more simultaneous queries.

	Benefits from: disk space for Apache caching.

* **PostgreSQL**
	Main attribute: disk space.
	
	Upscaling (more X-Road instances): additional disk space.
	Upscaling (more services): additional disk space and RAM to handle more daily logs
	Upscaling (more end users): additional RAM and CPUs for more simultaneous queries.
	Upscaling (over time): additional disk space to store more logs.
	
	Benefits from: decent disk I/O speed (fast HDD or SSD, preferably),
	fast connection to Anonymizer and Interface components.

## Logging and heartbeats

API and GUI daily logs are stored for a week by default at `${APPDIR}/${INSTANCE}/logs`
using TimedRotatingLogHandler.

API and GUI output heartbeats to
`${APPDIR}/${INSTANCE}/heartbeat/opendata-inteface-{gui,api}.json`
with the following formats:

```json
{"timestamp": "01-09-2017 15-31-13", "name": "Opendata API", "version": "0.0.1", "postgres": true}
{"timestamp": "01-09-2017 15-30-58", "name": "Opendata GUI", "version": "0.0.1", "api": true}
```

Heartbeats are output on a regular basis if no error occur,
depending on the **settings.py** `HEARTBEAT['interval']` value.

## Configuration

Interface is using Django framework and its configuration is defined in Django's
[settings.py](../../opendata_module/interface/interface/settings.py) file.

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo vi ${WEBDIR}/${INSTANCE}/opendata_module/interface/interface/settings.py
```

### Must be customized

#### Allowed hosts

Allowed hosts defines the valid host headers to [prevent Cross Site Scripting attacks](https://docs.djangoproject.com/en/1.11/topics/security/#host-headers-virtual-hosting).
_ALLOWED__HOSTS_ must include the domain name of the hosting server `opmon-opendata` (or IP address, if missing) or Django will
automatically respond with "Bad Request (400)".

```python
ALLOWED_HOSTS = ['opmon-opendata', 'localhost', '127.0.0.1']
```

**Note:** when getting **Bad request (400)** when accessing a page, then `ALLOWED_HOSTS` needs more tuning. 

#### PostgreSQL connection parameters

A Python dictionary defining the PostgreSQL connection parameters to a specific X-Road instance's opendata database.

The following example is for `sample` X-Road instance:

```python
POSTGRES_CONFIG = {
    'host_address': '127.0.0.1',
    'port': 5432,
    'database_name': 'opendata_sample',
    'table_name': 'logs',
    'user': 'interface_sample',
    'password': '${PWD_for_interface_sample}'
}
```

where ${PWD_for interface_sample} is password set to user `interface_sample` in section [Creating users and databases for X-Road instances](#creating-users-and-databases-for-x-road-instances)

**Note:** using `127.0.0.1` for the host, so that we could limit **opendata** PostgreSQL users' access to localhost. 


### Can be customized

#### Static root

Static root is necessary only for GUI and holds the CSS and JS files to serve through Apache after
`python manage.py collectstatic` has been issued. By default it directs to the Interface instance's root directory.

```python
STATIC_ROOT = '${WEBDIR}/${INSTANCE}/opendata_module/interface/static/'
```

#### Disclaimer

An arbitrary message in HTML format, which is displayed in the GUI footer and is also accompanying downloaded logs
via API as content of the `meta.json` file.

```python
DAYS = 10
DISCLAIMER = """<p>X-Road monitoring data is collected from Estonian X-Road members security servers available
by X-Road Center (Republic of Estonia Information System Authority, Riigi Infosüsteemi Amet, RIA)
and published as opendata with a delay of 10 days from actual transaction execution time.</p>
<p>Data is renewed nightly, between 0:00-6:00 (EET UTC+2h / EEST UTC+3h).</p>
<p>Timestamps (specifically <em>requestInTs</em>) are rounded to hour precision and presented in form of Unix timstamp (epoch time).</p>
<p>According to Security Authorities Act [1] §5 the security authorities are the
Estonian Internal Security Service and the Estonian Foreign Intelligence Service. Their authorizations are described in
chapter 4 (§21 - 35) of the above mentioned act. Based on aspects stated in the State Secrets and
Classified Information of Foreign States Act [2] §11 section 3, §7 p 10 and § 8 p 1 and in the
Public Information Act [3] §35 section 1 p 1, 31, 51 the X-Road usage statistics of security authorities is
considered to be for internal use only. X-Road data that is being published as open data by RIA does not contain
information about the security authorities.</p>

<ul style="list-style-type: none;">
<li>[1] <a href="https://www.riigiteataja.ee/en/eli/ee/521062017015/consolide/current" target="_new">Security Authorities Act</a></li>
<li>[2] <a href="https://www.riigiteataja.ee/en/eli/ee/519062017007/consolide/current" target="_new">Foreign States Act</a></li>
<li>[3] <a href="https://www.riigiteataja.ee/en/eli/ee/518012016001/consolide/current" target="_new">Public Information Act</li>
</ul>
""".format(DAYS)
```

#### Preview limit

Defines the maximum amout of logs which will be displayed in the GUI's "Preview" table.

```python
PREVIEW_LIMIT = 100
```

#### Logs directory and file parameters

Path to the directory which will store the rotating log files.

**Note:** directory must be created beforehand to enforce correct system level permissions.

```python
LOGS_DIR = '/srv/app/{0}/logs/'.format(X_ROAD_INSTANCE)
LOG['path'] = os.path.join(LOGS_DIR, 'log_opendata_interface_{0}.json'.format(X_ROAD_INSTANCE))
LOG['name'] = 'opendata_module - interface'
LOG['max_file_size'] = 2 * 1024 * 1024
LOG['backup_count'] = 10
LOG['level'] = logging.INFO
```

#### Heartbeat parameters

A Python dictionary defining heartbeat interval and files' path.

```python
HEARTBEAT = {
    'interval': 3600,
    'api_path': os.path.join(BASE_DIR, 'heartbeat', 'opendata_API_interface_sample.json'),
    'gui_path': os.path.join(BASE_DIR, 'heartbeat', 'opendata_GUI_interface_sample.json')
}
```

**Note:** *Interval* is the maximum period in seconds after which another heartbeat is generated, if no errors have occured.

**Note:** heartbeats directory must be created beforehand to enforce correct system level permissions.

### Shouldn't be customized

#### Field data YAML

YAML file containing data about the fields. Most notably field descriptions and data types (used for data type specific operations).

**Note:** must be ~identical to Anonymizer's.

```python
FIELD_DATA_YAML = os.path.join(BASE_DIR, 'cfg_lists', 'field_data.yaml')
```

#### Secret key

A hash seed enforced by Django. It has no real impact on the current solution, as no authentication is handled by Django,
nor do we use sessions of which hash could be stolen.