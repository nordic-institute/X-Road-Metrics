
| [![X-ROAD](./img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](./img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road Metrics - Open Data Module, Interface and PostgreSQL Node

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

This document covers the installation and configuration of the PostgreSQL database used by the [Opendata module](opendata_module.md).

## Networking

### Outgoing

The Opendata node needs no **outgoing** connections.

### Incoming

- The Opendata node accepts incoming connections from [Anonymizer module](anonymizer.md) (see also [Opendata module](../opendata_module.md)).
- The Opendata node accepts incoming access from the public (preferably HTTPS / port 443, but also redirecting HTTP / port 80).

## Installation

Opendata PostgreSQL is installed from the standard Ubuntu repository:
```bash
sudo apt update
sudo apt install postgresql
```


### Automatic PostgreSQL User Creation
The X-Road Metrics Opendata package includes a command that creates the PostgreSQL users automatically.
To create PostgreSQL users for X-Road instance *EX* run the following commands:

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
[Anonymizer module](anonymizer.md), according to the supplied configuration.

**Note:** PostgreSQL doesn't allow dashes and case sensitivity comes with a hassle.
This means that for PostgreSQL instance it is suggested to use underscores and lower characters. 
The `xroad-metrics-init-postgresql` does the required substitutions in usernames automatically.


### Allowing remote access

We need to enable remote access to PostgreSQL since Anonymizer and Networking modules might reside on another server.

In this example we assume that Anonymizer host IP is 172.31.0.1 and Networking host IP is 172.31.0.2.

Add the following lines to `/etc/postgresql/12/main/pg_hba.conf` in order to
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

Then edit the `/etc/postgresql/12/main/postgresql.conf` and change the *listen_addresses* to
```
listen_addresses = '*'
```

This says that PostgreSQL should listen on its defined port on all its network interfaces, 
including localhost and public available interfaces.

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Setting up rotational logging

PostgreSQL stores its logs by default in the directory `/var/lib/postgresql/12/main/pg_log/` specified in `/etc/postgresql/12/main/postgresql.conf`. 

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
