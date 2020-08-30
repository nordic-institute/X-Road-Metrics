
| [![Republic of Estonia Information System Authority](../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# Analysis Module

## Download

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

- The analysis module needs access to the [Database_Module](../database_module.md).

### Incoming

- The Analysis module's Interface accepts incoming access from the local network on http port 80 (and, if configured, also https port 443).

## 1. Installing Apache

Install Apache and relevant libraries in order to serve Interface.

```bash
sudo apt-get --yes update
sudo apt-get install --yes apache2 apache2-utils libexpat1 ssl-cert apache2-dev
```

**Note:** Apache installation creates user **www-data**. Django application, which serves Analyzer's Interface, is run with same permissions.

Open 80 (http) [and 443 (https) for Apache, if using SSL].

**WARNING:** **Although ufw is convenient, enabling it overrules/wipes the iptables, INCLUDING ACCESS TO 22 FOR SSH.** 
**Always allow 22 after enabling.** 


```bash
sudo apt-get install ufw
sudo ufw enable
sudo ufw allow 22
sudo ufw allow http
sudo ufw allow https
```

To verify that the ports are open, run

```bash
sudo ufw status
```

This should output something similar to

```bash
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

## 2. Installing Python and libraries

Analysis module has been written with Python 3.5.2 in mind, which is the default preinstalled _python3_ version for Ubuntu 16.04.3 LTS.
Although not tested, it should work with any modern Python 3.x version.

Most libraries follow the "MAJOR.MINOR.PATCH" schema, so the guideline is to review and update PATCH versions always (they mostly contain bug fixes). MINOR updates can be applied,  as they should keep compatibility, but there is no guarantee for some libraries. A suggestion would be to check if tests are working after MINOR updates and rollback if they stop working. MAJOR updates should not be applied.

Get _pip3_ tool for downloading 3rd party Python libraries for _python3_ along with system dependencies.

```bash
sudo apt-get --yes upgrade
sudo apt-get install --yes python3-pip libpq-dev libyaml-dev
pip3 install --upgrade pip
```

Install dependencies:

```bash
sudo pip3 install -r ${SOURCE}/analysis_module/requirements.txt
```

We also need our Python version specific *mod_wsgi* build to serve Python applications through WSGI and Apache.

```bash
sudo pip3 install mod_wsgi
```

This builds us a *mod_wsgi* for our *python3* version.

## 3. Configuring system users

The Interface uses the system user **www-data** (apache).
The Analyzer uses **analyzer** user.
Both of them share the same logs and heartbeat directory under group **opmon**
To create groups, users etc, execute:

```bash
sudo useradd --base-dir /opt --create-home --system --shell /bin/bash --gid analyzer analyzer
sudo groupadd --force opmon
sudo usermod --append --groups opmon www-data
sudo usermod --append --groups opmon analyzer
```

## 4. Create relevant X-Road instances

Each X-Road instance needs its own instance of Analyzer and Interface.

In this manual, `sample` is used as INSTANCE. 
To repeat for another instance, please change `sample` to map your desired instance.

```bash
# By default, Analyzer component will be installed to ${APPDIR}/${INSTANCE}
# By default, Interface component will be installed to ${WEBDIR}/${INSTANCE}
export APPDIR="/srv/app"
export WEBDIR="/var/www"
export INSTANCE="sample"
```

Logs and heartbeats for Analyzer and Interface share common directories in `${APPDIR}/${INSTANCE}`, therefor we set them as owned by `root:opmon` and writable for group `opmon`.

```bash
# Create log and heartbeat directories with group 'opmon' write permission
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo mkdir --parents ${APPDIR}/${INSTANCE}
sudo mkdir --parents ${APPDIR}/${INSTANCE}/logs
sudo mkdir --parents ${APPDIR}/${INSTANCE}/heartbeat
sudo chown root:opmon ${APPDIR}/${INSTANCE} ${APPDIR}/${INSTANCE}/logs ${APPDIR}/${INSTANCE}/heartbeat
sudo chmod g+w ${APPDIR}/${INSTANCE} ${APPDIR}/${INSTANCE}/logs ${APPDIR}/${INSTANCE}/heartbeat
```

Set up Analyzer computations codebase for the instance's scheduled computations:

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo mkdir --parents ${APPDIR}/${INSTANCE}/analysis_module

# Copy the Analyzer code from repository to the ${APPDIR}/${INSTANCE}.
sudo cp --recursive --preserve \
    ${SOURCE}/analysis_module/analyzer \
    ${APPDIR}/${INSTANCE}/analysis_module
```

Settings for Analyzer computations of different X-Road instances have been prepared and can be used:

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo rm --force ${APPDIR}/${INSTANCE}/analysis_module/analyzer/settings.py
sudo ln --symbolic \
    ${APPDIR}/${INSTANCE}/analysis_module/analyzer/instance_configurations/settings_${INSTANCE}.py \
    ${APPDIR}/${INSTANCE}/analysis_module/analyzer/settings.py
```

Correct necessary permissions for Analyzer computations:

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo chown --recursive analyzer:analyzer ${APPDIR}/${INSTANCE}/analysis_module
sudo chmod --recursive -x+X ${APPDIR}/${INSTANCE}/analysis_module
```

Set up Analyzer codebase for the instance's user interface (UI), web application:

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo mkdir --parents ${WEBDIR}/${INSTANCE}/analysis_module

# Copy the UI code from repository to the default Apache directory ($WEBDIR)
sudo cp --recursive --preserve \
    ${SOURCE}/analysis_module/analyzer_ui \
    ${WEBDIR}/${INSTANCE}/analysis_module
```

Set up database directory to store Django's internal SQLite database for UI.

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
# sudo mkdir --parents ${WEBDIR}
# sudo mkdir --parents ${WEBDIR}/${INSTANCE}
# sudo mkdir --parents ${WEBDIR}/${INSTANCE}/analysis_module
# sudo mkdir --parents ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui
sudo mkdir --parents ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/database
sudo chown www-data:www-data ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/database
```

Settings for Analyzer Interface (Analyzer UI) of different X-Road instances have been prepared and can be used:

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo rm --force ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/analyzer_ui/settings.py
sudo ln --symbolic \
    ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/instance_configurations/settings_${INSTANCE}.py \
    ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/analyzer_ui/settings.py
```

Correct necessary permissions for Analyzer Interface:

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo chown --recursive www-data:www-data ${WEBDIR}/${INSTANCE}/analysis_module
sudo chmod --recursive -x+X ${WEBDIR}/${INSTANCE}/analysis_module
```

## 5. Setting up Django SQLite databases for Interface

Interface (Analyzer UI) runs on Django.

In order for Django application to work, the internal SQLite database must be set up. For that, create schemas and then create corresponding tables:

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo --user www-data python3 ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/manage.py makemigrations
sudo --user www-data python3 ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/manage.py migrate
```

### Collecting static files for Apache

Static files are scattered during the development in Django. 
To allow Apache to serve the static files from one location, they have to be collected (copied to a single directory). 
Collect static files for relevant instances to `${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/static` by default (`STATIC_ROOT` value in `settings.py`):

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo --user www-data python3 ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/manage.py collectstatic <<<yes
```

Make the _root:root_ static directory explicitly read-only for others (including _www-data_):

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo chown --recursive root:root ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/static
sudo chmod --recursive o-w ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/static
sudo chmod --recursive g-w ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/static
```

## 6. Configuring Django

Configuration file is located at and can be modified:

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo vi ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/analyzer_ui/settings.py 
```

### Allowed hosts

Allowed hosts defines the valid host headers to [prevent Cross Site Scripting attacks](https://docs.djangoproject.com/en/1.11/topics/security/#host-headers-virtual-hosting). _ALLOWED__HOSTS_ must include the domain name of the hosting server (or IP address, if missing) or Django will automatically respond with "Bad Request (400)".

```python
ALLOWED_HOSTS = ['opmon-analyzer', 'localhost', '127.0.0.1']
```

**Note:** when getting **Bad request (400)** when accessing a page, then `ALLOWED_HOSTS` needs more tuning. 

### Static root

Static root is necessary only for GUI and holds the CSS and JS files to serve through Apache after `python manage.py collectstatic` has been issued. By default it directs to the Interface instance's root directory.

```python
# WEBDIR="/var/www"; INSTANCE="sample"
STATIC_ROOT = '{0}/{1}/analysis_module/analyzer_ui/static/'.format(WEBDIR, INSTANCE)
```

## 7. Configuring Apache

Let Apache know of the correct WSGI instance by replacing Apache's default mod_wsgi loader.

```bash
sudo cp --preserve /etc/apache2/mods-available/wsgi.load{,.bak}
sudo mod_wsgi-express install-module | head --lines 1 > /etc/apache2/mods-available/wsgi.load
```

Create an Apache configuration file at **/etc/apache2/sites-available/analyzer.conf** for port 80 (http). 

**Note:** To configure port 443 (https), public domain address and certificates are required.

**Note:** The correct Python interpreter is derived from the loaded *wsgi_module*.

```bash
sudo vi /etc/apache2/sites-available/analyzer.conf
```

**Note:** `hostname -I` is probably the easiest way to get opmon-analyzer server's IP address for `<machine IP>`

**Note:** `<machine IP>` can be substituted with public domain name, once it's acquired.

```bash
<VirtualHost <machine IP>:80>
        ServerName <machine IP>
        ServerAdmin yourname@yourdomain
        
        ErrorLog ${APACHE_LOG_DIR}/analysis-error.log
        CustomLog ${APACHE_LOG_DIR}/analysis-access.log combined

        LoadModule wsgi_module "/usr/lib/apache2/modules/mod_wsgi-py35.cpython-35m-x86_64-linux-gnu.so"

        WSGIApplicationGroup %{GLOBAL}

        #### Interface instances ####

        ## SAMPLE ##

        WSGIDaemonProcess sample
        WSGIScriptAlias /sample /var/www/sample/analysis_module/analyzer_ui/analyzer_ui/wsgi.py process-group=sample

        # Suffices to share static files only from one X-Road instance, as instances share the static files.
        Alias /static /var/www/sample/opendata_module/interface/static

        <Directory /var/www/sample/opendata_module/interface/static>
                Require all granted
        </Directory>
        
</VirtualHost>
```

After we have defined our *VirtualHost* configuration, we must enable the new *site* --- *analyzer.conf* --- so that Apache could start serving it.

```bash
sudo a2ensite analyzer.conf
```

We need to reload Apache in order for the site update to apply.

```bash
sudo service apache2 reload
```

## 8. Configuring database parameters

Change `MDB_PWD` and `MDB_SERVER` parameters in settings files:

```bash
# export WEBDIR="/var/www"; export INSTANCE="sample"
sudo vi ${WEBDIR}/${INSTANCE}/analysis_module/analyzer_ui/analyzer_ui/settings.py 
```

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo vi ${APPDIR}/${INSTANCE}/analysis_module/analyzer/settings.py 
```

## 9. Initial calculations

As a first step, the historic averages need to be calculated and the anomalies found. Both of these steps take some time, depending on the amount of data to be analyzed. For instance, given 6.2 million queries in the `clean_data`, the model training step takes approximately 10 minutes and anomaly finding step takes approximately 30 minutes.

### Training the models

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo --user analyzer python3 ${APPDIR}/${INSTANCE}/analysis_module/analyzer/train_or_update_historic_averages_models.py
```

### Finding anomalies

```bash
# export APPDIR="/srv/app"; export INSTANCE="sample"
sudo --user analyzer python3 ${APPDIR}/${INSTANCE}/analysis_module/analyzer/find_anomalies.py
```

## 10. Accessing web interface

Navigate to http://opmon-analyzer/${INSTANCE}/

## 11. CRON usage

It is suggested to run these two scripts automatically using CRON. 
For example, to run both scripts once every day at 06:00AM, do the following steps.

1) Open the CRON tab under the analyzer user:

```bash
sudo crontab -e -u analyzer
```

2) Add line:

```bash
0 6 * * * export APPDIR="/srv/app"; export INSTANCE="sample"; cd ${APPDIR}/${INSTANCE}/analysis_module/analyzer; python3 train_or_update_historic_averages_models.py; python3 find_anomalies.py
```

or as an alternative, all stuff within one bash script (please edit variable INSTANCE in this script, also ensure it is executable `chmod +x /srv/app/sample/analysis_module/analyzer/cron_analyzer.sh`

```
0 6 * * * export APPDIR="/srv/app"; export INSTANCE="sample"; ${APPDIR}/${INSTANCE}/analysis_module/analyzer/cron_analyzer_${INSTANCE}.sh
```

NB! The scripts to run might take long time, depending from dataset available (period to analyze, number of uniq query pairs within period). 
It is suggested to add some additional locking mechanism there to avoid simultaneous run.

## 12. Description and usage of Analyzer (the back-end)

### Models

In the core of the Analyzer are *models* that are responsible for detecting different types of anomalies. The model classes are located in the folder **analysis_module/analyzer/models**.

1. **FailedRequestRatioModel.py** (anomaly type 4.3.1): aggregates requests for a given service call by a given time interval (e.g. 1 hour) and checks if the ratio of failed requests (```succeeded=False```) with respect to all requests in this time interval is larger than a given threshold. The type of found anomalies (```anomalous_metric```) will be failed_request_ratio.

2. **DuplicateMessageIdModel.py** (anomaly type 4.3.2):  aggregates requests for a given service call by a given time interval (e.g. 1 day) and checks if there are any duplicated ```messageId``` in that time interval. The type of found anomalies (```anomalous_metric```) will be duplicate_message_id.

3. **TimeSyncModel.py** (anomaly type 4.3.3): for each request, checks if the time of data exchange between client and producer is a positive value. Namely, an incident is created if ```requestNwSpeed < 0``` or ```responseNwSpeed < 0```. In each incident, the number of requests not satisfying these conditions are aggregated for a given service call and a given time interval (e.g. 1 hour). The type of found anomalies (```anomalous_metric```) will be one of [responseNwDuration, requestNwDuration].

4. **AveragesByTimeperiodModel.py** (anomaly types 4.3.5-4.3.9) :  aggregates requests for a given service call by a given time interval, calculating:
1) the number or requests in this time interval,
2) mean request size (if exists --- ```clientRequestSize```, otherwise ```producerRequestSize```) in this time interval,
3) mean response size (if exists --- ```clientResponseSize```, otherwise ```producerResponseSize```) in this time interval,
4) mean client duration (```totalDuration```) in this time interval,
5) mean producer duration (```producerDurationProducerView```) in this time interval.
Each of these metrics are compared to historical values for the same service call during a similar time interval (e.g. on the same weekday and the same hour). In particular, the model considers the mean and the standard deviation (std) of historical values and calculates the *z-score* for the current value: ```z_score = abs(current_value - historic_mean) / historic_std```.
Based on this score, the model estimates the confidence that the current value comes from a different distribution than the historic values. If the confidence is higher than a specified confidence threshold, the current value is reported as a potential incident. The type of found anomalies (```anomalous_metric```) will be one of [request_count, mean_request_size, mean_response_size, mean_client_duration, mean_producer_duration].
 
### Scripts

Before finding anomalies using the AveragesByTimeperiodModel, the model needs to be trained. Namely, it needs to calculate the historic means and standard deviations for each relevant time interval. The data used for training should be as "normal" (anomaly-free) as possible. Therefore, it is recommended that the two phases, training and finding anomalies, use data from different time periods. To ensure these goals, the **regular** processes for anomaly finding and model training proceed as follows:

1. For recent requests, the existing model is used to *find* anomalies, which will be recorded as potential incidents. The found anomalies are shown in the Interface (Analyzer UI) for a specified time period (e.g. 10 days), after which they are considered "expired" and will not be shown anymore.
2. Anomalies/incidents that have expired are used to update (or retrain) the model. Requests that are part of a "true incident" (an anomaly that was marked as "incident" before the expiration date) are not used to update the model. This way, the historic averages remain to describe the "normal" behaviour. Note that updating the model does not change the anomalies that have already been found (the existing anomalies are not recalculated).

Also, as these processes aggregate requests by certain time intervals (e.g. hour), only the data from time intervals that have already completed are used. This is to avoid situations where, for example, the number of requests within 10 minutes is compared to the (historic) number of requests within 1 hour, as such comparison would almost certainly yield an anomaly. 

It is recommended that the model is given some time to learn the behaviour of a particular service call (e.g. 3 months). Therefore, the following approach is implemented for **new** service calls:
1. For the first 3 months since the first request was made by a given service call, no anomalies are reported (this is the training period)
2. After these 3 months have passed, the first anomalies for the service call will be reported. Both the model is trained (i.e. the historic averages are calculated) and anomalies are found using the same data from the first 3 months.
3. The found anomalies are shown in the analyzer user interface for 10 days, during which their status can be marked. During these 10 days, the model version is fixed and incoming data are analyzed (i.e. the anomalies are found) based on the initial model (built on the first 3-months data).
4. After these 10 days (i.e. when the first incidents have expired), the model is retrained, considering the feedback from the first anomalies and the **regular** analyzer process is started (see above).


The approach described above is implemented in two scripts, located in the folder **analysis_module/analyzer**:

1. **train_or_update_historic_averages_models.py:** takes requests that have appeared (and expired as potential incidents) since the last update to the model, and uses them to update or retrain the model to a new version.
2. **find_anomalies.py:** takes new requests that have appeared since the last anomaly-finding phase was performed and uses the current version of the model to find anomalies, which will be recorded as potential incidents. 

### Performance

To estimate the performance of the Analyzer, the following tables provide time measurements on instances `instance1` and `instance2`.

##### 1) train_or_update_historic_averages_models.py

| instance   |      # service calls      |  # service calls past training period | total # queries in clean data |  determining service call stages time | training time (hour_weekday) | training time (weekday) | total time |
|:----------:|:-------------:|:------:|:------:|:------:|:------:|:------:|:------:|
| instance1 | 4200 | 1987 | 6,200,000 | 3 min | 4 min | 3 min | 10 min |
| instance2 | 2156 | 441 | 12,000,000 | 8 min | 7 min | 6 min| 21 min |


##### 2) find_anomalies.py

| instance   |      # service calls      |  # service calls past training period | total # queries in clean data |  FRR* time | DM* time | TS* time | service call stages time | HA* time (hour_weekday) | HA* time (weekday) | total time |
|:----------:|:-------------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|:------:|
| instance1 | 4200 | 1987 | 6,200,000 | 4 min | 3 min | 3 min | 5 min | 6 min | 6 min | 27 min |
| instance2 | 2156 | 441 | 12,000,000 | 7 min | 6 min | 7 min | 11 min | 15 min | 11 min | 57 min |

\* Abbreviations:

* FRR - failed request ratio model
* DM - duplicate message id model
* TS - time sync errors model
* HA - historic averages model
