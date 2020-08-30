
| [![Republic of Estonia Information System Authority](img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Database Module

## About

The **Database module** is part of [X-Road v6 monitor project](../README.md), which includes modules of Database module (this document), [Collector module](collector_module.md), [Corrector module](corrector_module.md), [Analysis module](analysis_module.md), [Reports module](reports_module.md), [Opendata module](opendata_module.md) and [Networking/Visualizer module](networking_module.md).

The **Database module** provides storage and synchronization between the other modules. 

Overall system, its users and rights, processes and directories are designed in a way, that all modules can reside in one server (different users but in same group 'opmon') but also in separate servers. 

Overall system is also designed in a way, that allows to monitor data from different X-Road v6 instances (in Estonia `ee-dev`, `ee-test`, `EE`, see also [X-Road v6 environments](https://moodle.ria.ee/mod/page/view.php?id=700).

Overall system is also designed in a way, that can be used by X-Road Centre for all X-Road members as well as for Member own monitoring (includes possibilities to monitor also members data exchange partners).

## Installation

The database is implemented with the MongoDB technology: a non-SQL database with replication and sharding capabilities.

This document describes the installation steps for Ubuntu 16.04. For other Linux distribution, please refer to: [MongoDB 3.4 documentation](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/)

Add the MongoDB repository key and location:

```bash
# Key 4096R/A15703C6 2016-01-11 [expires: 2020-01-05]
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" \
    | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
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
sudo service mongod status
```

To start MongoDB daemon, run:

```bash
sudo service mongod start
```

To ensure that MongoDB daemon start is enabled after system start, run and check, that `/lib/systemd/system/mongod.service; enabled` is present:

```bash
sudo service mongod status
# Loaded: loaded (/lib/systemd/system/mongod.service; disabled; ...)
```

If not, then enable and restart MongoDB daemon:

```bash
sudo systemctl enable mongod.service
# Created symlink from /etc/systemd/system/multi-user.target.wants/mongod.service \
#    to /lib/systemd/system/mongod.service.
sudo service mongod restart
sudo service mongod status
# Loaded: loaded (/lib/systemd/system/mongod.service; enabled; ...)
```

### User Configuration

The database module requires the creation of the following users: 

* A **root** user to controls the configuration of the database.
* A backup specific user to backup data collections.
* A superuser to personalize access to the configuration of the database.
* Module specific users, to provide access and limit permissions.
* Optionally, creation of a test user for Integration Tests with the database.
* Optionally, creation of a read-only user for reviewing the database.

#### Configure root user

Enter MongoDB client shell:

```bash
mongo
```

Inside the MongoDB client shell, create the **root** user in the **admin** database. 
Replace **ROOT_PWD** with the desired root password (keep it in your password safe).

```
use admin
db.createUser( { user: "root", pwd: "ROOT_PWD", roles: ["root"] })
```

#### Configure backup user

Inside the MongoDB client shell, create the **db_backup** user in the **admin** database. 
Replace **BACKUP_PWD** with the desired password (keep it in your password safe).

```
use admin
db.createUser( { user: "db_backup", pwd: "BACKUP_PWD", roles: ["backup"] })
```

#### Configure superuser

When applicable, create inside the MongoDB client shell one or more personalized **superuser** user in the **admin** database. 
Replace **superuser** with the personalized user name in your domain. 
Replace **SUPERUSER_PWD** with the desired password (keep it in your password safe).

```
use admin
db.createUser( { user: "superuser", pwd: "SUPERUSER_PWD", roles: ["root"] })
```

The instructions below describes the creation of module users for **collector**, **corrector**, **reports**, **analyzer**, and **anonymizer** modules.

**Note 1:** The instructions assume `sample` instances. For other instances replace the `sample` suffix appropriately. 
X-Road instance names in Estonia are case-sensitive (sample: `EE` differs from `ee`).

**Note 2:** MongoDB database names and settings in different modules should follow this case-sensitivity as well to guarantee, that publishing and notification scripts in [Reports module](reports_module.md) can use correct path.
Please refer to the specific configuration file of every module and set the MongoDB access to match the user and passwords created here, where:

- INSTANCE: is the X-Road v6 instance
- MONGODB_USER: is the instance-specific module user
- MONGODB_PWD: is the MONGODB_USER password 
- MONGODB_SERVER: is the database host (example: `opmon`)
- MONGODB_SUFFIX: is the database suffix, same as INSTANCE

#### Configure collector module user

Inside the MongoDB client shell, create the **collector_sample** user in the **auth_db** database. 
Replace **MODULE_PWD** with the desired module password.
The collector user has "readWrite" permissions to "query_db" and "collector_state" databases (here, **query_db_sample** and **collector_state_sample**).

```
use auth_db
db.createUser( { user: "collector_sample", pwd: "MODULE_PWD", roles: []})
db.grantRolesToUser( "collector_sample", [{ role: "readWrite", db: "query_db_sample"}])
db.grantRolesToUser( "collector_sample", [{ role: "readWrite", db: "collector_state_sample"}])
```

#### Configure corrector module user

Inside the MongoDB client shell, create the **corrector_sample** user in the **auth_db** database. 
Replace **MODULE_PWD** with the desired module password.
The corrector user has "readWrite" permissions to "query_db" database (here, **query_db_sample**).

```
use auth_db
db.createUser( { user: "corrector_sample", pwd: "MODULE_PWD", roles: []})
db.grantRolesToUser( "corrector_sample", [{ role: "readWrite", db: "query_db_sample"}])
```

#### Configure reports module user

Inside the MongoDB client shell, create the **reports_sample** user in the **auth_db** database. 
Replace **MODULE_PWD** with the desired module password.
The reports user has "read" permissions to "query_db" database and "readWrite" permission to "reports_state" database (here, **query_db_sample** and **reports_state_sample**).

```
use auth_db
db.createUser({ user: "reports_sample", pwd: "MODULE_PWD", roles: [] })
db.grantRolesToUser( "reports_sample", [{ role: "read", db: "query_db_sample" }])
db.grantRolesToUser( "reports_sample", [{ role: "readWrite", db: "reports_state_sample" }])
```

#### Configure analyzer module users

Analyzer module has two sub-modules, calculation ('training or updateing historic average models' and 'finding anomalies') and web interface. 
It is suggested to have separate users for them although the access rights are the same. 
Web interface user needs access to the query database as well because list of queries, that belong to an anomaly are loaded from there.

##### Configure analyzer module calculation user

Inside the MongoDB client shell, create the **analyzer_sample** user in the **auth_db** database. 
Replace **MODULE_PWD** with the desired module password.
The analyzer user has "read" permissions to "query_db" database and "readWrite" permission to "analyzer_database" database (here, **query_db_sample** and **analyzer_database_sample**).

```
use auth_db
db.createUser({ user: "analyzer_sample", pwd: "MODULE_PWD", roles: [] })
db.grantRolesToUser( "analyzer_sample", [{ role: "read", db: "query_db_sample" }])
db.grantRolesToUser( "analyzer_sample", [{ role: "readWrite", db: "analyzer_database_sample" }])
```

##### Configure analyzer module interface user

Inside the MongoDB client shell, create the **analyzer_interface_sample** user in the **auth_db** database. 
Replace **MODULE_PWD** with the desired module password.
The analyzer interface user has "read" permissions to "query_db" database and "readWrite" permission to "analyzer_database" database (here, **query_db_sample** and **analyzer_database_sample**).

```
use auth_db
db.createUser({ user: "analyzer_interface_sample", pwd: "MODULE_PWD", roles: [] })
db.grantRolesToUser( "analyzer_interface_sample", [{ role: "read", db: "query_db_sample" }])
db.grantRolesToUser( "analyzer_interface_sample", [{ role: "readWrite", db: "analyzer_database_sample" }])
```

#### Configure anonymizer module user

Inside the MongoDB client shell, create the **anonymizer_sample** user in the **auth_db** database. 
Replace **MODULE_PWD** with the desired module password.
The anonymizer user has "read" permissions to "query_db" database (here, **query_db_sample**) and "readWrite" permissions to "anonymizer_state" database (here **anonymizer_state_sample**).

```
use auth_db
db.createUser({ user: "anonymizer_sample", pwd: "MODULE_PWD", roles: [] })
db.grantRolesToUser( "anonymizer_sample", [{ role: "read", db: "query_db_sample" }])
db.grantRolesToUser( "anonymizer_sample", [{ role: "readWrite", db: "anonymizer_state_sample" }])
```

#### Configure ci_test user (optional)

The **ci_test** user is only necessary to run integration tests that uses MongoDB (example, corrector integration tests). The integration tests uses as MONGODB_SUFFIX the value `PY-INTEGRATION-TEST`, and this should not be mixed with any module specific user.

Inside the MongoDB client sehll, create the **ci_test** user in the **auth_db** database. The default password is also "ci_test". The **ci_test** user has permissions ONLY to databases:

- CI_query_db
- CI_collector_state
- CI_reports_state
- CI_analyzer_database

**Note:** The integration database uses a different name convention to avoid conflict with real MONGODB_SUFFIX instances.

```
use auth_db
db.createUser({ user: "ci_test", pwd: "ci_test", roles: [] })
db.grantRolesToUser( "ci_test", [{ role: "dbOwner", db: "CI_query_db" }])
db.grantRolesToUser( "ci_test", [{ role: "dbOwner", db: "CI_collector_state" }])
db.grantRolesToUser( "ci_test", [{ role: "dbOwner", db: "CI_reports_state" }])
db.grantRolesToUser( "ci_test", [{ role: "dbOwner", db: "CI_analyzer_database" }])
```

#### Configure read-only user (optional)

Inside the MongoDB client shell, create the **user_read** user in the **admin** database. 
Replace **USER_PWD** with the desired password (keep it in your password safe).

```
use admin
db.createUser( { user: "user_read", pwd: "USER_PWD", roles: ["readAnyDatabase"] })
```

#### Check user configuration and permissions

To check if all users and configurations were properly created, list all users and verify their roles using the following commands:

Inside the MongoDB client shell:

```
use admin
db.getUsers()
use auth_db
db.getUsers()
```

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

#### Enable MongoDB authentication

MongoDB default install does not enable authentication. The following steps are used to configure MongoDB security authorization.

**NOTE:** The **root** user (database **admin**) needs to exist already. See section ['Configure root user'](#configure-root-user).

To enable MongoDB security authorization, edit the **mongod.conf** configuration file using your favorite text editor (here, **vi** is used).

```bash
sudo vi /etc/mongod.conf
```

Change the following line in the configuration file:

```
security:
    authorization: enabled
```

After saving the alterations, the MongoDB service needs to be restarted. This can can be performed with the following command:

```bash
sudo service mongod restart
```

**Note:** After enabling authentication it will be needed to specify database, user and password when connecting to mongo client shell. For example:

```bash
mongo admin --username root --password
# or
mongo admin --username user_read --password
# or
mongo auth_db --username collector_sample --password
```

#### Enable access from other machines

To make MongoDB services available in the modules network (see System Architecture)[system_architecture.md], the following configuration is necessary:

Open MongoDB configuration file in your favorite text editor (here, **vi** is used)

```bash
sudo vi /etc/mongod.conf
```

Add the external IP (the IP seen by other modules in the network) to enable the IP biding. 
In this example, if the machine running MongoDB (`opmon`) has the Ethernet IP `10.11.22.33`, and therefore, the following line is edited in the configuration file:

```
bindIp: 127.0.0.1,10.11.22.33
```

After saving the alterations, the MongoDB service needs to be restarted. This can can be performed with the following command:

```bash
sudo service mongod restart
```

### Network Configuration

The MongoDB interface is exposed by default in the port **27017**.
Make sure the port is allowed in the firewall configuration.

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

### MongoDB Structure: databases, collections

#### Index Creation

Although indexes can improve query performances, indexes also present some operational considerations. See [MongoDB Operational Considerations for Indexes](https://docs.mongodb.com/manual/core/data-model-operations/#data-model-indexes) for more information.

Our collection holds a large amount of data, and our applications need to be able to access the data while building the index, therefor we consider building the index in the background, as described in [Background Construction](https://docs.mongodb.com/manual/core/index-creation/#index-creation-background).

The example here uses the INSTANCE-specific database `query_db_sample`, and the same procedure should be used to other / additional instances. 

Enter MongoDB client as root:

```bash
mongo admin --username root --password 
```

Inside MongoDB client shell, execute the following commands:

```
use query_db_sample
db.raw_messages.createIndex({'corrected': 1, 'requestInTs': 1})
db.clean_data.createIndex({'clientHash': 1})
db.clean_data.createIndex({'producerHash': 1})
db.clean_data.createIndex({'correctorTime': 1})
db.clean_data.createIndex({'correctorStatus': 1, 'client.requestInTs': 1 })
db.clean_data.createIndex({'correctorStatus': 1, 'producer.requestInTs': 1 })
db.clean_data.createIndex({'messageId': 1, 'client.requestInTs': 1})
db.clean_data.createIndex({'messageId': 1, 'producer.requestInTs': 1})
db.clean_data.createIndex({'client.requestInTs': 1})
db.clean_data.createIndex({'client.serviceCode': 1})
db.clean_data.createIndex({'producer.requestInTs': 1})
db.clean_data.createIndex({'producer.serviceCode': 1})
db.clean_data.createIndex({'client.clientMemberCode': 1, 'client.clientSubsystemCode': 1, 'client.requestInTs': 1})
db.clean_data.createIndex({'client.serviceMemberCode': 1, 'client.serviceSubsystemCode': 1, 'client.requestInTs': 1})
db.clean_data.createIndex({'producer.clientMemberCode': 1, 'producer.clientSubsystemCode': 1, 'producer.requestInTs': 1})
db.clean_data.createIndex({'producer.serviceMemberCode': 1, 'producer.serviceSubsystemCode': 1, 'producer.requestInTs': 1})

use collector_state_sample
db.server_list.createIndex({ 'timestamp': -1})

use reports_state_sample
db.notification_queue.createIndex({'status': 1, 'user_id': 1})

use analyzer_database_sample
db.incident.createIndex({'incident_status': 1, 'incident_creation_timestamp': 1})
```

**Note 1**: If planning to select / filter records manually according to different fields, then please consider to create index for every field to allow better results.
From other side, if these are not needed, please consider to drop them as the existence reduces overall speed of [Corrector module](corrector_module.md).

**Note 2**: Additional indexes might required for system scripts in case of functionality changes (eg different reports). 
Please consider to create them as they speed up significantly the speed of [Reports module](reports_module.md).

**Note 3**: Index build might affect availability of cursor for long-running queries.
Please review the need of active [Collector module](collector_module.md) and specifically the need of active [Corrector module](corrector_module.md) while running long-running queries, specifically [Reports module](reports_module.md#usage).

## Additional Tools

Additional helping scripts, directory `mongodb_scripts/` has been included into source code repository.
To fetch it: 

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
ls -al ${SOURCE}/mongodb_scripts/
```

NB! Mentioned appendixes do not log their work and do not keep heartbeat.

### Speed

Scripts `read_speed_test.py`, `hash_speed_test.py` are available.

Commands:

```bash
export INSTANCE="sample"
cd ${SOURCE}/mongodb_scripts/
python3 read_speed_test.py query_db_${INSTANCE} root --auth admin --host 127.0.0.1:27017
python3 hash_speed_test.py query_db_${INSTANCE} root --auth admin --host 127.0.0.1:27017
```

### Indexes

It might happen, that under heavy and continuos write activities to database, the indexes corrupt. 
In result, read access from database takes long time, it can be monitored also from current log file `/var/log/mongodb/mongod.log`, where in COMMANDs the last parameter protocol:op_query  in milliseconds (ms) is large even despite usage of indexes (planSummary: IXSCAN { }).

In such cases, dropping and creating indexes again or reIndex() process might be the solution.
It may also be worth running if the collection size has changed significantly or if the indexes are consuming a disproportionate amount of disk space.
These operations may be expensive for collections that have a large amount of data and/or a large number of indexes.
Please consult with MongoDB documentation.

Commands:

```
mongo admin --username root --password
> use query_db_sample
> db.raw_messages.reIndex()
> db.clean_data.reIndex()

> use collector_state_sample
> db.server_list.reIndex()

> use reports_state_sample
> db.notification_queue.reIndex()

> use analyzer_database_sample
> db.incident.reIndex()
exit
```

Additional tools `create_indexes_query.py`, `create_indexes_reports.py`, `create_indexes_collector.py` and `create_indexes_analyzer.py` are available.

Commands:

```bash
export INSTANCE="sample"
cd ${SOURCE}/mongodb_scripts/
python3 create_indexes_query.py query_db_${INSTANCE} root --auth admin --host 127.0.0.1:27017
python3 create_indexes_collector.py collector_state_${INSTANCE} root --auth admin --host 127.0.0.1:27017
python3 create_indexes_reports.py reports_state_${INSTANCE} root --auth admin --host 127.0.0.1:27017
python3 create_indexes_analyzer.py analyzer_database_${INSTANCE} root --auth admin --host 127.0.0.1:27017
```

### Purge records from MongoDB raw data collection after available in clean_data

To keep MongoDB size under control, save the MongoDB / HDD space, the optional `raw_data_archive.py` script can be used. 
It archives processed data ({"corrected": true}) from raw data, and remove the documents from database.

Commands:

```bash
export INSTANCE="sample"
cd ${SOURCE}/mongodb_scripts/
python3 raw_data_archive.py query_db_${INSTANCE} root --auth admin --host 127.0.0.1:27017
```

## Monitoring and Status

MongoDB runs as a daemon process. It is possible to stop, start and restart the database with the following commands:

* Check stop

```bash
sudo service mongod stop
```

* Check start

```bash
sudo service mongod start
```

* Check restart

```bash
sudo service mongod restart
```

* Check status

```bash
sudo service mongod status
```

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

For example, to perform a complete database backup, execute (replace `BACKUP_PWD` with the password for backup user set in section ['Configure backup user'](#configure-backup-user) and `MDB_BKPDIR` is output directory for backup):

```bash
export MDB_BKPDIR="/srv/backup/mongodb-`/bin/date '+%Y-%m-%d_%H:%M:%S'`" 
mkdir --parents ${MDB_BKPDIR} 
mongodump --username db_backup --password 'BACKUP_PWD' --authenticationDatabase admin --oplog --gzip --out ${MDB_BKPDIR}
```

For example, to perform a database restore, execute (replace `BACKUP_PWD` with the password for backup user set in section ['Configure backup user'](#configure-backup-user) and `MDB_BKPDIR` is directory for backup):

```bash
mongorestore --username db_backup --password 'BACKUP_PWD' --authenticationDatabase admin --oplogReplay --gzip ${MDB_BKPDIR}
```

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

To make mongod instance as master, the following commands are needed in mongod shell (in this example, if the machine running MongoDB (`opmon`) has the Ethernet IP `10.11.22.33`):

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

