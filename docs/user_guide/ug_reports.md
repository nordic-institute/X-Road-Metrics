|  [![X-ROAD](../img/xroad-metrics-100.png)](https://x-road.global/) | ![European Union / European Regional Development Fund / Investing in your future](../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road reports user guide

## License <!-- omit in toc -->

This document is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit <https://creativecommons.org/licenses/by-sa/4.0/>

## General

The reports are primarily meant for IT administrators responsible for certain
subsystems.

The reports should give them an overview of what is happening on X-Road
concerning the subsystem:

* How many requests are sent to their subsystem and by who (**produced
  services**)
* How many requests their subsystem is making and to who (**consumed services**)

Both of these are in turn separated into two, the so-called "real services" and
[X-Road metaservices](#what-are-metaservices).

All four tables contain the following information by services:

* The client/producer
* The amount of successful/unsuccessful queries
* The duration of successful queries
* The request and response sizes in bytes

We believe, that the reports are useful for gaining a better overview of your
customers and data-exchange partners. The reports should give and overview of
the following aspects:

* The most used services
* The services with the most faults
* The longest running and fastest running services
* The largest responses

These statistics can prove useful in designing better services, provide insight
into how to best use the services as well as estimating hardware requirements.

Each report contains a unique part in the filename (unix timestamp) and the
e-mail notification that is sent out only contains a reference to the report.

When setting up an environment and the directory tree, the following things
should be considered:

* Each recipient should only be able to see the report that was sent to them
* No other person should be able to view other reports
* When the institution has changed administrators, the new administrator should
  now have access to old reports without the previous administrator forwarding
  the references to him
* And administrator that has left the institution should no longer recieve
  notifications about new reports

Reports are generated in all configured environments based on the `cron`
configuration.

## Frequently asked questions

### The report contains incorrect data

**Question: The report shows that service S has been used X times, however
according to our data the amount of requests should be a lot larger. Why are
they not reflected in the report?**

The basis of the reports is the accessibility of the members Security Servers
for Metrics software. In case your Security Server was not accessible for one
reason or another, your report will be generated based on the information
provided by the other members Security Servers that have exchanged data with
you. It is possible, that those Security Servers were also not accessible for a
period.

Possible reasons for why the Metrics software might be unable to access X-Road
members Security Servers are listed under the [Technical](#technical) section.

### What is the duration and how is it calculated?

The duration is set and show in the report from the clients perspective. This
means that it is calculated as the delta between the timestamp that the Security
Server returns the response to the informationsystem and the timestamp that the
informationsystem sent the request out (Client ResponseOutTs - Client
RequestInTs). The duration is represented in milliseconds.

In case your Security Server does not provide this data, it will not be
represented in the report (it is shown as `None`).

The following is a picture depicting which timestamps are used from the
different data-exchange partners Security Servers and where for the
calculations.

![Timestamps](0_timestamps.png "Timestamps")

#### The request duration from the consumers point of view

The duration of the X-Road request from a consumers point of view is calculated
as a delta between the response timestamp of the X-Road Security Server serving
the consumer subsystem (8) and the timestamp of the request from the clients
informationsystem arriving at the clients Security Server (1).

```text
totalDuration = Client responseOutTs (8) - Client requestInTs (1)
```

#### The request duration from the producers point of view

The duration of the X-Road request from a producers point of view is calculated
as a delta between the timestamp of the response from the producers Security
Server to the consumers Security Server (6) and the timestamp of the consumers
Security Server request arriving at the consumers Security Server (3).

```text
producerDurationProducerView = Producer responseOutTs (6) - Producer requestInTs (3)
```

### What are `metaservices`

Metaservices are services that provide informatin about the X-Road instance or
the services located on it. An example of these are the `listMethods`, `getWsdl`
ja `getOpenAPI` metaservices.

More information about metaservices can be found in the main X-Road repository:

* [X-Road: Service Metadata
  Protocol](https://github.com/nordic-institute/X-Road/blob/master/doc/Protocols/pr-meta_x-road_service_metadata_protocol.md)
* [X-Road: Service Metadata Protocol for
  REST](https://github.com/nordic-institute/X-Road/blob/master/doc/Protocols/pr-mrest_x-road_service_metadata_protocol_for_rest.md)

In the context of reports, we also consider the services used for environmental
and operational monitoring as metaservices. These include:
`getSecurityServerMetrics`, `getSecurityServerOperationalData` and
`getSecurityServerHealthData`.

### How is this data collected?

The X-Road [operational
monitoring](https://github.com/nordic-institute/X-Road/tree/master/doc/OperationalMonitoring)
is used for gathering data, more specifically, we use the
`getSecurityServerOperationalData` service.

Example requests and a selection of scripts is also available in the
[systemtests/op-monitoring](https://github.com/nordic-institute/X-Road/tree/master/src/systemtest/op-monitoring)
directory in the main X-Road repository.

The collected data does not include the content of the requests.

## Technical

In order to collect monitoring data from Security Servers, please ensure that:

* The members are using an up to date Security Server package
* The Security Servers being monitored allow access from the Security Server
  used by Metrics on ports 5500 and 5577.
* Check that the Security Servers being monitored have the operational
  monitoring addon installed:

  ```bash
  sudo dpkg -l | egrep "xroad" | sort
  ```

  If the addon is correctly installed, it should be prefixed with `ii`.

  If something is wrong, it is prefixed with something else such as `iU` or `iF`
  ([see here for more
  information](https://askubuntu.com/questions/18804/what-do-the-various-dpkg-flags-like-ii-rc-mean))

  ```bash
  ii xroad-addon-hwtokens <version> all X-Road AddOn: hwtokens
  ii xroad-addon-messagelog <version> all X-Road AddOn: messagelog
  ii xroad-addon-metaservices <version> all X-Road AddOn: metaservices
  ii xroad-addon-opmonitoring <version> all X-Road AddOn: operations monitoring service
  ii xroad-addon-proxymonitor <version> all X-Road AddOn: proxy monitoring metaservice
  ii xroad-addon-wsdlvalidator <version> all X-Road AddOn: wsdlvalidator
  ii xroad-common <version> amd64 X-Road shared components
  ii xroad-monitor <version> all X-Road monitoring service
  ii xroad-opmonitor <version> all X-Road operations monitoring daemon
  ii xroad-proxy <version> all X-Road security server
  ii xroad-securityserver <version> all X-Road security server
  ```
