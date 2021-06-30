
| [![X-ROAD](../img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# Analyzer Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## Installation

This sections describes the necessary steps to install the **analyzer module** on a Ubuntu 20.04 Linux host. For a complete overview of different modules and machines, please refer to the ==> [System Architecture](../system_architecture.md) <== documentation.


### Add X-Road OpMon Package Repository for Ubuntu
TODO

### Install Analyzer Package
To install opmon-analyzer and all dependencies execute the commands below:

```bash
sudo apt-get update
sudo apt-get install opmon-analyzer
```

The installation package automatically installs following items:
 * opmon-analyzer command to run the analyzer manually
 * Linux user named _opmon_ and group _opmon_
 * settings file _/etc/opmon/analyzer/settings.yaml_
 * cronjob in _/etc/cron.d/opmon-analyzer-cron_ to run analyzer automatically every three hours
 * log folders to _/var/log/opmon/analyzer/_

Only _opmon_ user can access the settings files and run opmon-analyzer command.

To use opmon-analyzer you need to fill in your X-Road and MongoDB configuration into the settings file.
Refer to section [Analyzer Configuration](#analyzer-configuration)


## Usage

### Analyzer Configuration

To use analyzer you need to fill in your X-Road and MongoDB configuration into the settings file.
(here, **vi** is used):

```bash
sudo vi /etc/opmon/analyzer/settings.yaml
```

Settings that the user must fill in:
* X-Road instance name
* username and password for the analyzer module MongoDB user

To run analyzer for multiple X-Road instances, a settings profile for each instance can be created. For example to have profiles DEV, TEST and PROD create three copies of `setting.yaml` 
file named `settings_DEV.yaml`, `settings_TEST.yaml` and `settings_PROD.yaml`.
Then fill the profile specific settings to each file and use the --profile
flag when running opmon-analyzer. For example to run model update using the TEST profile:
```
opmon-analyzer --profile TEST upate
```

`opmon-analyzer` command searches the settings file first in current working direcrtory, then in
_/etc/opmon/analyzer/_

### Manual usage

All analyzer module actions can be executed by calling the `opmon-analyzer` command.
Command should be executed as user `opmon` so change to that user:
```bash
sudo su opmon
```

The Analyzer program runs in two separate stages that can be started by the commands below:
```bash
opmon-analyzer update                     # Train or update the analyzer data models
opmon-analyzer find                       # Find anomalies in the service call data
```

Both of these steps take some time, depending on the amount of data to be analyzed. 
For instance, given 6.2 million queries in the `clean_data`, the model training step takes approximately 10 minutes 
and anomaly finding step takes approximately 30 minutes.


Above example commands use the default settings file. To use another settings profile, you can use --profile flag:
```bash
opmon-analyzer --profile TEST update
opmon-analyzer --profile TEST find
```

### Cron settings
Default installation includes a cronjob in _/etc/cron.d/opmon-analyzer-cron_ that runs analyzer every two hours. This job runs analyzer using default settings profile (_/etc/opmon/analyzer/settings.yaml_)

If you want to change the analyzer cronjob scheduling or settings profiles, edit the file e.g. with vi
```
vi /etc/cron.d/opmon-analyzer-cron
```
and make your changes. For example to run analyzer every six hours using settings profiles PROD and TEST:
```bash
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# m   h  dom mon dow  user       command
  40 */6  *   *   *   opmon     opmon-analyzer --profile PROD update && opmon-analyzer --profile PROD find
  20 */6  *   *   *   opmon     opmon-analyzer --profile TEST update && opmon-analyzer --profile TEST find
```

If analyzer is to be run only manually, comment out the default cron task by adding the '#' character:
```bash
#   40 */2  *   *   *   opmon     opmon-analyzer update && opmon-analyzer find
```

## Implementation Details

### Models

In the core of the Analyzer are *models* that are responsible for detecting different types of anomalies. The model classes are located in the folder **analysis_module/analyzer/models**.

1. **FailedRequestRatioModel.py** (anomaly type 4.3.1): 
aggregates requests for a given service call by a given time interval (e.g. 1 hour) and
checks if the ratio of failed requests (```succeeded=False```) with respect to all 
requests in this time interval is larger than a given threshold. 
The type of found anomalies (```anomalous_metric```) will be failed_request_ratio.

2. **DuplicateMessageIdModel.py** (anomaly type 4.3.2):
aggregates requests for a given service call by a given time interval (e.g. 1 day) and 
checks if there are any duplicated ```messageId``` in that time interval. 
The type of found anomalies (```anomalous_metric```) will be duplicate_message_id.

3. **TimeSyncModel.py** (anomaly type 4.3.3): 
for each request, checks if the time of data exchange between client and producer is a 
positive value. Namely, an incident is created if 
```requestNwSpeed < 0``` or ```responseNwSpeed < 0```. 
In each incident, the number of requests not satisfying these conditions are aggregated for a 
given service call and a given time interval (e.g. 1 hour). 
The type of found anomalies (```anomalous_metric```) will be one of 
[responseNwDuration, requestNwDuration].

4. **AveragesByTimeperiodModel.py** (anomaly types 4.3.5-4.3.9) : 
aggregates requests for a given service call by a given time interval, calculating:

    1) the number or requests in this time interval,
    2) mean request size 
    (if exists --- ```clientRequestSize```, otherwise ```producerRequestSize```) in this time interval,
    3) mean response size 
    (if exists --- ```clientResponseSize```, otherwise ```producerResponseSize```) in this time interval,
    4) mean client duration 
    (```totalDuration```) in this time interval,
    5) mean producer duration 
    (```producerDurationProducerView```) in this time interval.

Each of these metrics are compared to historical values for the same service call 
during a similar time interval (e.g. on the same weekday and the same hour). 
In particular, the model considers the mean and the standard deviation (std) of historical 
values and calculates the *z-score* for the current value: 

```z_score = abs(current_value - historic_mean) / historic_std```

Based on this score, the model estimates the confidence that the current value comes from a 
different distribution than the historic values. 
If the confidence is higher than a specified confidence threshold, the current value 
is reported as a potential incident. The type of found anomalies (```anomalous_metric```) 
will be one of 
[request_count, mean_request_size, mean_response_size, mean_client_duration, mean_producer_duration].
 
### Scripts

Before finding anomalies using the AveragesByTimeperiodModel, the model needs to be trained. 
Namely, it needs to calculate the historic means and standard deviations for each 
relevant time interval. The data used for training should be as "normal" (anomaly-free) as possible. 
Therefore, it is recommended that the two phases, training and finding anomalies, 
use data from different time periods. 

To ensure these goals, the **regular** processes for anomaly finding and 
model training proceed as follows:

1. For recent requests, the existing model is used to *find* anomalies, which will be 
recorded as potential incidents. 
The found anomalies are shown in the Interface (Analyzer UI) for a specified 
time period (e.g. 10 days), after which they are considered "expired" and will not be shown anymore.

2. Anomalies/incidents that have expired are used to update (or retrain) the model.
Requests that are part of a "true incident" 
(an anomaly that was marked as "incident" before the expiration date) 
are not used to update the model. 
This way, the historic averages remain to describe the "normal" behaviour. 
Note that updating the model does not change the anomalies that have already been found 
(the existing anomalies are not recalculated).

Also, as these processes aggregate requests by certain time intervals (e.g. hour), 
only the data from time intervals that have already completed are used. This is to avoid situations where, 
for example, the number of requests within 10 minutes is compared to the (historic) number of requests within 1 hour, 
as such comparison would almost certainly yield an anomaly. 

It is recommended that the model is given some time to learn the behaviour of a particular service call (e.g. 3 months). 
Therefore, the following approach is implemented for **new** service calls:
1. For the first 3 months since the first request was made by a given service call, 
no anomalies are reported (this is the training period)
2. After these 3 months have passed, the first anomalies for the service call will be reported. 
Both the model is trained (i.e. the historic averages are calculated) and anomalies are found 
using the same data from the first 3 months.
3. The found anomalies are shown in the analyzer user interface for 10 days, during which their status can be marked. 
During these 10 days, the model version is fixed and incoming data are analyzed (i.e. the anomalies are found) 
based on the initial model (built on the first 3-months data).
4. After these 10 days (i.e. when the first incidents have expired), 
the model is retrained, considering the feedback from the first anomalies and the **regular** analyzer process 
is started (see above).


### Performance

To estimate the performance of the Analyzer, the following tables provide time measurements 
on instances `instance1` and `instance2`.

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
