
| [![X-ROAD](../img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |



# Analyzer Module

## Installation

This sections describes the necessary steps to install the **analyzer module** on an Ubuntu 20.04 Linux host. For a complete overview of different modules and machines, please refer to the ==> [System Architecture](../system_architecture.md) <== documentation.

### Firewall Setup
Opmon Analyzer User Interface is hosted on an Apache web server.
To access the web app, you need to allow incoming HTTPS requests in the host machine's firewall.

**IMPORTANT:** The instructions below can be applied on a host machine that is used only to run Opmon Analyzer.
On a shared host contact the system administrator and follow your networking environment's security policies.

**WARNING:** Although ufw is convenient, enabling it overrules/wipes the iptables, **INCLUDING PORT 22 FOR SSH.** 
If you need SSH access to the server make sure to allow port 22 in ufw settings. 


**TODO: Verify these instructions**

```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow https
sudo ufw enable
```

To list the open ports, run

```bash
sudo ufw status
```


### Add X-Road OpMon Package Repository for Ubuntu
TODO

### Install Analyzer Package
To install opmon-analyzer and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install opmon-analyzer-ui
```

The installation package automatically installs following items:
 * Linux users _opmon_ and _www-data_
 * opmon-analyzer-ui Django web-application package
 * Apache web server and dependencies
 * Apache configuration file for the web-app _/etc/apache2/conf-available/opmon-analyzer-ui.conf_
 * a self signed SSL certificate
 * web-app static content under _/usr/share/opmon/analyzer_ui_
 * web-app dynamic content under _/var/lib/opmon/analyzer_ui_
 * settings file _/etc/opmon/analyzer_ui/settings.yaml_
 * log folders to _/var/log/opmon/analyzer_ui/_

Only users in _opmon_ group can access the settings files.

You have to fill in some environment specific settings to the settings file to make the Analyzer User Interface work properly.
Refer to section [Analyzer User Interface Configuration](#analyzer-user-interface-configuration)

## Usage
### Analyzer User Interface Configuration

To use analyzer user interface you need to fill in your X-Road, MongoDB and Django configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/opmon/analyzer/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* username and password for the analyzer-interface MongoDB user
* secret key for the Django web-app
* allowed hostname(s) for the web-app server

### Hostname configuration
The Apache Virtual Host configuration defines the hostname for the Analyzer UI service.
The Analyzer UI module installer fills in the current hostname to Apache config file automatically.

If your hostname changes after installation, or the installer used wrong hostname, you can change the value by editing 
the Apache config file `/etc/apache2/sites-available/opmon-analyzer-ui.conf`. 
For example if your hostname is `myhost.mydomain.org` 
change the contents of the file to:
```
Use OpmonOpendataVHost myhost.mydomain.org
```

After these changes you must restart Apache:
```bash
sudo apache2ctl restart
```

And then you can test accessing the Opmon Opendata UI by pointing your browser to `https://myhost.mydomain.org/`

The instructions above should be sufficient for simple use cases. 
For more advanced Apache configurations, e.g. to add more allowed alias names for the host, 
you need to modify the apache configuration template in `/etc/apache2/conf-available/opmon-analzer-ui.conf`.

### Settings profiles
The analyzer UI can show data for multiple X-Road instances using settings profiles. 
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

Navigate to https://opmon-analyzer/${INSTANCE}/

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
