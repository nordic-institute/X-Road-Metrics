
| [![Republic of Estonia Information System Authority](docs/img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](docs/img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](docs/img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project

## Introduction

The project maintains X-Road v6 log of service calls (queries). 
Logs are collected and corrected. 
Further analysis about anomalies (possible incidents) is made. 
Usage reports are created and published. 
Logs are anonymized and published as opendata.

Instructions to install all components, as well as all modules source code, can be found at:

```
https://github.com/ria-ee/X-Road-opmonitor
```

## Architecture

The system architecture is described ==> [here](./docs/system_architecture.md) <==.

## Installation instructions

### Installing/setting up the Mongo Database (MongoDB)

The **first thing** that should be done is setting up the MongoDB. 
Instructions on setting up the MongoDB can be found ==> [here](./docs/database_module.md) <==

### Module installation precedence

The modules should be set up in the following order:
 
1. [Collector](./docs/collector_module.md) (before others)
2. [Corrector](./docs/corrector_module.md) (after Collector, before others)
3. [Analyzer](./docs/analysis_module.md) (optional, after previous)
4. [Reports](./docs/reports_module.md) (optional, after previous)
5. [Opendata](./docs/opendata_module.md) (optional, after previous)
6. [Networking](./docs/networking_module.md) (optional, after Opendata)

## Programming language

All modules, except Networking, are written in [**Python**](https://www.python.org/)&trade; and tested with version 3.5.2. 
Other 3.x versions are likely to be compatible, give or take some 3rd party library interfaces.
Networking module is written in **R** [https://www.r-project.org/](https://www.r-project.org/).

## Reporting Issues / Contributing

Efforts have been made to ensure everything is easy, correct, secure. 
Please report any bugs and feature requests on the Github issue tracker. 
We will **read** all reports!

We also accept pull requests from forks. 
If possible please follow guidelines https://github.com/nordic-institute/X-Road-development/blob/master/WORKFLOW.md
Very grateful to accept contributions from folks.

## Stay Safe

We have every reason to believe this X-Road operational monitoring tool will not corrupt your data or harm your computer. 
But if we were you, we would suggest to test thoroughly before use it in a production environment.

Developed by: [STACC (Software Technology and Applications Competence Center)](https://www.stacc.ee/en/) according to procurement [RHR 183990](https://riigihanked.riik.ee/register/hange/183990)

Released by [Riigi Infosüsteemi Amet, Data Exchange Layer X-Road](https://www.ria.ee/en/state-information-system/x-tee.html), under the [MIT License](http://www.opensource.org/licenses/MIT).

## Contact

Product owner: Toomas Mölder, toomas.molder@ria.ee; (desk) +372 666 8822 / (mobile) +372 55 22000; skype: toomas.molder
