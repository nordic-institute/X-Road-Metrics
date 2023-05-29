
|  [![X-ROAD](img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Database Module

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## About

The **Database module** is part of [X-Road Metrics](../README.md), which includes the following modules:
 - [Database module](./database_module.md)
 - [Collector module](./collector_module.md)
 - [Corrector module](./corrector_module.md)
 - [Reports module](./reports_module.md)
 - [Anonymizer module](./anonymizer_module.md)
 - [Opendata module](./opendata_module.md)
 - [Networking/Visualizer module](./networking_module.md)
 - [Opendata Collector module](./opendata_collector_module.md)

The **Database module** provides storage and synchronization between the other modules.

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in one server (different users but in same group 'xroad-metrics') but also in separate servers.

Overall system is also designed in a way, that allows to monitor data from different X-Road instances (e.g. in Estonia there are three instances: `ee-dev`, `ee-test` and `EE`.)

Overall system is also designed in a way, that can be used by X-Road Centre for all X-Road members as well as for Member own monitoring (includes possibilities to monitor also members data exchange partners).

## Installation

The database is implemented with the MongoDB technology: a non-SQL database with replication and sharding capabilities.

This document describes the installation steps for Ubuntu 20.04 or Ubuntu 22.04.
You can also refer to official [MongoDB 4.4 installation instructions](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/) for Ubuntu 20.04.
Refer to official [MongoDB 6.0 installation instructions](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/) for Ubuntu 22.04.

## Add the MongoDB APT repository and signing key for Ubuntu 20.04

```bash
# Key rsa4096/20691eec35216c63caf66ce1656408e390cfb1f5 [expires: 2024-05-26]
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 656408e390cfb1f5
sudo apt-add-repository "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse"
```

## Add the MongoDB APT repository and signing key for Ubuntu 22.04

```bash
# Key rsa4096/39bd841e4be5fb195a65400e6a26b1ae64c3c388 [expires: 2027-02-22T]
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 6a26b1ae64c3c388
sudo apt-add-repository "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse"
```


Install MongoDB server and client tools (shell)

```bash
sudo apt-get update
sudo apt-get install --yes mongodb-org
```

Most libraries follow the "MAJOR.MINOR.PATCH" schema, so the guideline is to review and update PATCH versions always (they mostly contain bug fixes). MINOR updates can be applied,  as they should keep compatibility, but there is no guarantee for some libraries. A suggestion would be to check if tests are working after MINOR updates and rollback if they stop working. MAJOR updates should not be applied.

## Configuration

This section describes the necessary MongoDB configuration. It assumes that MongoDB is installed and running.
To check if the MongoDB daemon is active, run:

```bash
sudo systemctl status mongod.service
```

To enable and start MongoDB daemon, run:

```bash
sudo systemctl enable mongod.service
sudo systemctl start mongod.service
```

To restart MongoDB daemon (e.g. after configuration changes)
```bash
sudo systemctl restart mongod.service
```

### Enable Authentication
We want only authenticated users to have access to MongoDB.
To enable authentication, enter MongoDB shell:

#### For MongoDB 4.4 on Ubuntu 20.04

```bash
mongo
```

#### For MongoDB 6.0 on Ubuntu 22.04

```bash
mongosh
```

Issue the following commands to create a *root* user:
```
use admin
db.createUser(
  {
    user: "root",
    pwd: passwordPrompt(), // or cleartext password
    roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
  }
)
exit
```

Store the MongoDB root user password to a secure place, e.g. your password manager.

Edit the MongoDB config file with your favorite editor (vi used here). Add the following lines:
```yaml
security:
  authorization: enabled
```


In the same file also add the private IP-address of the server running MongoDB into the bindIp list.
This allows X-Road Metrics modules on other hosts to connect with MongoDB
```yaml
net:
  port: 27017
  bindIp: 127.0.0.1,<mongo server ip-address here>
```


Now restart the MongoDB daemon for the configuration changes to take effect:
```bash
sudo systemctl restart mongod.service
```


### Automatic User and Index Creation
Each X-Road Metrics module uses a different user to access MongoDB. This way the module access rights can be limited
to bare minimum. The MongoDB users for all modules can be created automatically by using an init command that is
installed with the X-Road Metrics Collector Module.

At this point, please refer to the [installation guide of X-Road Metrics Collector](./collector_module.md)
and install the collector package.

To run the X-Road Metrics MongoDB init command you need the following information:
 - the IP address or hostname of the MongoDB server
 - the name of the X-Road instance where you are collecting the data
 - password of the MongoDB root user crated above

In the example below we use *xroad-metrics-centraldb* as the hostname, *EX* as the X-Road instance and *mysecret* as
the password.

Open SSH terminal to the server where Collector module was installed and run the following commands:
```bash
sudo su xroad-metrics
xroad-metrics-init-mongo --host xroad-metrics-centraldb:27017 --user root --password mysecret EX
```

The command output includes a list of usernames and passwords generated:
```bash
Username               | Password     | Escaped Password
-----------------------+--------------+--------------------
analyzer_EX            | T34k^$rYOH7$ | "T34k^$rYOH7$"
analyzer_interface_EX  | R9U+u?9R$5!E | "R9U+u?9R$5!E"
anonymizer_EX          | U'7<^)0&-b8s | "U'7<^)0&-b8s"
collector_EX           | 7,zj3q1!CN#m | "7,zj3q1!CN#m"
corrector_EX           | kf^{E4G/4[f0 | "kf^{E4G/4[f0"
reports_EX             | Fdqay:76I}x5 | "Fdqay:76I}x5"
```

Store the output to a secure location, e.g. to your password manager. These usernames and passwords are needed later
to configure the X-Road Metrics modules. The 'Escaped Password' column contains the password in YAML
escaped format that can be directly added to the config files.

The command also creates default MongoDB indexes needed by the X-Road Metrics modules. For more information about
the indexes, see chapter [Indexes](#Indexes).


### Manually Create Optional Users
This Chapter can be skipped unless you want to install the optional users for integration test or read-only use.
To manually add users to MongoDB, enter MongoDB client shell:

```bash
mongo
```

#### **read-only user (optional)**

Inside the MongoDB client shell, create the **user_read** user in the **admin** database.
Replace **USER_PWD** with the desired password (keep it in your password safe).

```
use admin
db.createUser( { user: "user_read", pwd: "USER_PWD", roles: ["readAnyDatabase"] })
```

### Check user configuration and permissions

To check if all users and configurations were properly created, list all users and verify their roles using
the following commands inside the MongoDB client shell:

```
use admin
db.getUsers()
use auth_db
db.getUsers()
```

For X-Road instance `EX` auth_db should have following users and access rights:

* **anonymizer_EX**:
    * query_db_EX: read
    * anonymizer_state_EX: readWrite
* **collector_EX**:
    * query_db_EX: readWrite,
    * collcetor_state_EX: readWrite
* **corrector_EX**:
    * query_db_EX: readWrite
* **reports_EX**:
    * query_db_EX: read,
    * reports_state_EX: 'readWrite'


### MongoDB Configuration

#### Enable Rotate Log Files

Inside mongo client shell, execute the following command to enable log rotation:

```
use admin
db.runCommand( { logRotate : 1 } )
exit
```

To ensure, that daily logfiles are kept, we suggest to use logrotate. Please add file `/etc/logrotate.d/mongodb`

```bash
sudo vi /etc/logrotate.d/mongodb
```

with content:

```yaml
/var/log/mongodb/mongod.log {
  daily
  rotate 30
  compress
  dateext
  notifempty
  missingok
  sharedscripts
  postrotate
    /bin/kill -SIGUSR1 `pgrep mongod` 2> /dev/null || true
  endscript
}
```


### Network Configuration

MongoDB default port is **27017**.
Following modules need to have access to MongoDB:
    - Collector
    - Corrector
    - Reports
    - Anonymizer


### Establish encrypted SSL/TLS client connection

Every module has own settings to use secure connection to MongoDB.
Database server has to be preconfigured to accept encrypted connection from client side.
See https://www.mongodb.com/docs/manual/reference/program/mongod/#options for details.

To enable TLS connection from client side, configure `mongodb` section in
module's settings file. Example:
```
mongodb:
  host: host
  user: user
  password: *****
  tls: True
  tls-ca-file: /path/to/ca/pem/file
```

### Log Configuration

The default MongoDB install uses the following folders to store data and logs:

Data folder:

```
/var/lib/mongodb
```

Log files:

```
/var/log/mongodb
```

## Database Structure

### Indexes

The `xroad-metrics-init-mongo` command documented in chapter [Automatic User and Index Creation](#Automatic User and Index Creation)
creates a default set of indexes to MongoDB. If your application needs some further indexes, those can be added in the MongoDB shell.

Although indexes can improve query performances, indexes also present some operational considerations.
See [MongoDB Operational Considerations for Indexes](https://docs.mongodb.com/manual/core/data-model-operations/#data-model-indexes) for more information.
Our collection holds a large amount of data, and our applications need to be able to access the data while building the
index, therefore we consider building the index in the background, as described in
[Background Construction](https://docs.mongodb.com/manual/core/index-creation/#index-creation-background).


**Note 1**: If planning to select / filter records manually according to different fields, then please consider to create index for every field to allow better results.
From other side, if these are not needed, please consider to drop them as the existence reduces overall speed of [Corrector module](corrector_module.md).

**Note 2**: Additional indexes might required for system scripts in case of functionality changes (eg different reports).
Please consider to create them as they speed up significantly the speed of [Reports module](reports_module.md).

**Note 3**: Index build might affect availability of cursor for long-running queries.
Please review the need of active [Collector module](collector_module.md) and specifically the need of active [Corrector module](corrector_module.md) while running long-running queries, specifically [Reports module](reports_module.md#usage).

### Index Recreation

It might happen, that under heavy and continuos write activities to database, the indexes corrupt.
In result, read access from database takes long time, it can be monitored also from current log file `/var/log/mongodb/mongod.log`, where in COMMANDs the last parameter protocol:op_query  in milliseconds (ms) is large even despite usage of indexes (planSummary: IXSCAN { }).

In such cases, dropping and creating indexes again or reIndex() process might be the solution.
It may also be worth running if the collection size has changed significantly or if the indexes are consuming a disproportionate amount of disk space.
These operations may be expensive for collections that have a large amount of data and/or a large number of indexes.
Please consult with MongoDB documentation.

Commands:

```
mongo admin --username root --password
> use query_db_EX
> db.raw_messages.reIndex()
> db.clean_data.reIndex()

> use collector_state_EX
> db.server_list.reIndex()

> use reports_state_EX
> db.notification_queue.reIndex()

> use analyzer_database_EX
> db.incident.reIndex()
exit
```

### Purge records from MongoDB raw data collection after available in clean_data

To keep MongoDB size under control, save the MongoDB / HDD space, it might be useful to clean up raw_data that has
already been processed by the corrector (`{"corrected": true}`).


## MongoDB Compass

It is also possible to monitor MongoDB with a GUI interface using the MongoDB Compass.
For specific instructions, please refer to:

```
https://www.mongodb.com/products/compass
```

and for a complete list of MongoDB monitoring tools, please refer to:

```
https://docs.mongodb.com/master/administration/monitoring/
```

## Database backup

To perform backup of database, it is recommended to use the mongodb tools **mongodump** and **mongorestore**

For additional details and recommendations about MongoDB backup and restore tools, please check:

```
https://docs.mongodb.com/manual/tutorial/backup-and-restore-tools/
```

## Database replication

MongoDB supports replication. A replica set in MongoDB is a group of mongod processes that maintain the same data set.
Replica sets provide redundancy and high availability, and are the basis for all production deployments.

Sample to add replication, add the following line in the configuration file:


```bash
sudo vi /etc/mongod.conf
```

```
replication:
    replSetName: rs0
    oplogSizeMB: 100
```

After saving the alterations, the MongoDB service needs to be restarted. This can can be performed with the following command:

```bash
sudo service mongod restart
```

To make mongod instance as master, the following commands are needed in mongod shell
(in this example, if the machine running MongoDB has the Ethernet IP `10.11.22.33`):

```
> rs.initiate()
{
        "info2" : "no configuration specified. Using a default configuration for the set",
        "me" : "10.11.22.33:27017",
        "ok" : 1
}
```

To build or rebuild indexes for a replica set, see [Build Indexes on Replica Sets](https://docs.mongodb.com/manual/tutorial/build-indexes-on-replica-sets/#index-building-replica-sets).

For additional details and recommendations about MongoDB replication set, please check
[MongoDB Manual Replication](https://docs.mongodb.com/manual/replication/)

To change the size of oplog, follow the steps
provided in manual https://docs.mongodb.com/manual/tutorial/change-oplog-size/


## MongoDB performance, tuning

Please note, that performance of MongoDB and its tuning really depends on physical hardware, its drivers, HDD, CPU, RAM, SWP settings, operating system tunings etc.

The performance also depends on size of database, existing indexes and their sizes, how they fit into RAM. The solution with small amount of data (less than 100 millions rows, less than 10G data), speed of different queries is usually very good and satisfactory (less than a second) but might rapidly increase when data amount increases (up to 1 billion rows, up to 2T of data etc).

We cannot predict all the nyances here, please be prepared within your own team.

Some of the tunings that might be important follows:

### Warnings and recommendations of MongoDB

```
# mongo admin --username root --password
STORAGE  [initandlisten] ** WARNING: Using the XFS filesystem is strongly recommended with the WiredTiger storage engine
STORAGE  [initandlisten] **          See http://dochub.mongodb.org/core/prodnotes-filesystem
CONTROL  [initandlisten]
CONTROL  [initandlisten] ** WARNING: You are running on a NUMA machine.
CONTROL  [initandlisten] **          We suggest launching mongod like this to avoid performance problems:
CONTROL  [initandlisten] **              numactl --interleave=all mongod [other options]
CONTROL  [initandlisten]
CONTROL  [initandlisten] ** WARNING: /sys/kernel/mm/transparent_hugepage/enabled is 'always'.
CONTROL  [initandlisten] **        We suggest setting it to 'never'
CONTROL  [initandlisten]
CONTROL  [initandlisten] ** WARNING: /sys/kernel/mm/transparent_hugepage/defrag is 'always'.
CONTROL  [initandlisten] **        We suggest setting it to 'never'
```

### Disable ipv6 settings

Edit and add into `/etc/sysctl.conf`
```
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
```

### Virtual memory

Edit and add into `/etc/sysctl.conf`
```
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
```

### Swapiness

See also https://en.wikipedia.org/wiki/Paging#Swappiness

Edit and add into `/etc/sysctl.conf`
```
vm.swappiness = 1
# or max vm.swappiness = 10
```

### Set up Linux Ulimit

Edit and add into `/etc/security/limits.d/mongod.conf`
```
mongod       soft        nproc        64000
mongod       hard        nproc        64000
mongod       soft        nofile       64000
mongod       hard        nofile       64000
```

### Sharding
One way to improve MongoDB performance is to use [sharding](https://www.mongodb.com/basics/sharding). Setting
up a sharded MongoDB is currently not covered in this document.
