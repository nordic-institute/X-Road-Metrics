
| [![Republic of Estonia Information System Authority](../../img/ria_100_en.png)](https://www.ria.ee/en.html) [![X-ROAD](../../img/xroad_100_en.png)](https://www.ria.ee/en/state-information-system/x-tee.html) | ![European Union / European Regional Development Fund / Investing in your future](../../img/eu_rdf_100_en.png "Documents that are tagged with EU/SF logos must keep the logos until 1.11.2022. If it has not stated otherwise in the documentation. If new documentation is created  using EU/SF resources the logos must be tagged appropriately so that the deadline for logos could be found.") |
| :-------------------------------------------------- | -------------------------: |

# X-Road v6 monitor project - Open Data Module, API documentation

## About

Open Data API allows to query daily logs or log samples programmatically without the necessity to interact with the graphical user interface.

In order to achieve that, handlers allow to query the following data:

* Minimum and maximum date of the available logs;
* Column names, types, descriptions and available oeprators;
* All daily logs in **tar.gz** format;
* Sample logs for a day in **JSON** format.

URL below is used as 

```bash
export INSTANCE="sample"
export URL="https://logs.x-tee.ee/${INSTANCE}"
# or http:// when security certificate not in place yet)
```

### Response codes

* **[200]** - Expected response has been delivered.
* **[400]** - Malformed query: consult the given documentation and 	response message.
* **[500]** - Query was fine, but something went wrong internally (a bug has slipped past): consult administrator.

### Error format

All API error messages are in JSON format and look similar to

```json
{"error": "error message"}
```

### Supported HTTP/HTTPS request methods

API supports all the HTTP/HTTPS request methods:

* GET
* POST (and its derivates)

**Note:** all resources (handlers) are available for both GET and POST type of requests.

POST expects query to be in JSON format and be the whole request body. 

## Handlers

### Minimum and maximum date

Logs can only be downloaded on a daily basis. The handler provides a date range, from which it is sensible to query.

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
curl --get --url "${URL}/api/date_range"
```

There's also a POST version:

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
curl --request --url "${URL}/api/date_range"
```

#### Parameters

None

#### Returns

Minimum and maximum date of the logs in the database, sample:

```json
{"date": {"min": "2017-09-19", "max": "2017-09-25"}}
```

### Column data

It is possible to provide several data column specific parameters when querying daily logs. This handler gives an overview of the columns.

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
curl --get --url "${URL}/api/column_data"
```

There's also a POST version:

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
curl --request --url "${URL}/api/column_data"
```

#### Parameters

None

#### Returns

Metadata of the existing columns.

```json
{"columns": [
    {"type": "string", "valid_operators": ["=", "!="], "name": "clientSubsystemCode", "description": "Subsystem code of the X-Road member (client)"},
    {"type": "integer", "valid_operators": ["=", "!=", "<", "<=", ">", ">="], "name": "responseAttachmentCount", "description": "Number of attachments of the response"},
    {"type": "string", "valid_operators": ["=", "!="], "name": "clientMemberCode", "description": "Member code of the X-Road member (client)"},
    {"type": "string", "valid_operators": ["=", "!="], "name": "serviceMemberClass", "description": "Member class of the X-Road member (service provider)"},
    {"type": "integer", "valid_operators": ["=", "!=", "<", "<=", ">", ">="], "name": "id", "description": "Unique identifier of the record"}, 
    {"type": "string", "valid_operators": ["=", "!="], "name": "securityServerType", "description": "Type of the security server"}, 
    {"type": "string", "valid_operators": ["=", "!="], "name": "serviceMemberCode", "description": "Member code of the X-Road member (service provider)"},
    {"type": "integer", "valid_operators": ["=", "!=", "<", "<=", ">", ">="], "name": "responseSoapSize", "description": "Size of the response (bytes)"},
    {"type": "boolean", "valid_operators": ["=", "!="], "name": "succeeded", "description": "True, if request mediation succeeded, false otherwise."},
    ...
]}
```

### Logs sample

Retrieve first PREVIEW_LIMIT = 100 logs, which have matched the query, in JSON format.

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
curl --get --url "${URL}/api/logs_sample"
```

There's also a POST version:

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
curl --request --url "${URL}/api/logs_sample"
```

#### Parameters

**date** (mandatory)

Specifies the day of which logs are fetched.

> **type:** string
> **format**: YYYY-MM-DD
> **example:** `{"date": "2017-09-21"}`

**columns** (optional)

Specifies the columns to return.

_Note:_ If missing or an empty list, all available columns are included.

> **type:** list of strings
> **example:** `{"columns": ["clientMemberCode", "clientSubsystemCode", "succeeded"]}`

**constraints** (optional)

Specifies the criteria which the returned logs must meet. 

_Note:_  If missing or an empty list, no constraints will be applied to the logs other than the date and all the day's logs are returned.

> **type:** list of JSON objects
> **format:** `{"column": "columnName", "operator": "validOperator", "value": "someValue"}`
> > **column:** name of the column
> > **operator:** valid operator for the column's data type (`"=", "!=", "<", "<=", ">", ">="`)
> **example:** `{"constraints": [{"operator": "=", "value": "70006317", "column": "clientMemberCode"}, {"operator": "=", "value": "monitoring", "column": "clientSubsystemCode"}]}`

**order clauses** (optional)

Specifies the order in which to return the logs.

_Note:_ If missing or an empty list, logs are ordered by "id".
_Note:_ Different order clauses may return different logs, depending on whether database optimizer first limits or first orders the queried data.

> **type:** list of JSON objects
> **format:** `{"column": "columnName", "order: "asc|desc"}`

#### Returns

JSON object with "data" key holding list of logs. 
Each log is represented as a list with deterministic column order (in the same order as the columns were provided). 
If columns were not provide, the order is identical to the column order from [column data](#column-data).

```json
{"data": [
	["4905", "001e90e8-c1c4-4edc-80a4-1a0f8945774a", "2017-09-21", "3", "True", "113"],
	["10325", "00336a85-1a72-48e4-bf5a-215c3f9af497", "2017-09-21", "3", "True", "146"],
	["155975", "004061a2-7e6f-48cf-9d30-e43c26e7b763", "2017-09-21", "3", "True", "148"],
	...
]}
```

#### Example query

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
# export DATE=$(date -d "10 days ago" '+%Y-%m-%d')
curl --get --url "${URL}/api/logs_sample" \
    --data-urlencode "date=${DATE}" \
    --data-urlencode "columns=[\"id\", \"requestInDate\", \"responseAttachmentCount\", \"succeeded\", \"totalDuration\"]" \
    --data-urlencode "constraints=[{\"column\": \"totalDuration\", \"operator\": \"<=\", \"value\": \"150\"}]" \
    --data-urlencode "order-clauses=[{\"column\":\"totalDuration\",\"order\":\"asc\"}]"
```

The same in POST version:

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
# export DATE=$(date -d "10 days ago" '+%Y-%m-%d')
curl --request --url "${URL}/api/logs_sample" \
    --header "Content-Type:application/json" \
    --data "{\"date\": \"${DATE}\", \
           \"columns\": [\"id\", \"requestInDate\", \"responseAttachmentCount\", \"succeeded\", \"totalDuration\"], \
           \"constraints\": [{\"column\": \"totalDuration\", \"operator\": \"<=\", \"value\": \"150\"}], \
           \"order-clauses\": [{\"column\": \"totalDuration\", \"order\": \"asc\"}]}"
```

### Daily logs

Retrieve all logs for a specified date in a **tar.gz** archive. The archive consists of two files:

* **YYYY-MM-DD.json**
* **meta.json**

#### Parameters

Identical to [logs' sample](#logs-sample).

#### Returns

Binary file with MIME type "application/gzip".

#### Example query

GET version:

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
# export DATE=$(date -d "10 days ago" '+%Y-%m-%d')

TEMPFILE=$(tempfile)
curl --get --url "${URL}/api/daily_logs" \
    --data-urlencode "date=${DATE}" \
    --data-urlencode "columns=[\"id\", \"requestInDate\", \"responseAttachmentCount\", \"succeeded\", \"totalDuration\"]" \
    --data-urlencode "constraints=[{\"column\": \"totalDuration\", \"operator\": \"<=\", \"value\": \"150\"}]" \
    --data-urlencode "order-clauses=[{\"column\": \"totalDuration\", \"order\": \"asc\"}]"
    > ${TEMPFILE}

tar tzvf ${TEMPFILE} # See download content
# tar xzvf ${TEMPFILE} # Unpack / extract download content
/bin/rm --force ${TEMPFILE}
```

There's also a POST version:

```bash
# export INSTANCE="sample"; export URL="https://logs.x-tee.ee/${INSTANCE}"
# export DATE=$(date -d "10 days ago" '+%Y-%m-%d')

TEMPFILE=$(tempfile)
curl --request --url "${URL}/api/daily_logs" \
    --header "Content-Type:application/json" \
    --data "{\"date\": \"${DATE}\", \
           \"columns\": [\"id\", \"requestInDate\", \"responseAttachmentCount\", \"succeeded\", \"totalDuration\"], \
           \"constraints\": [{\"column\": \"totalDuration\", \"operator\": \"<=\", \"value\": \"150\"}], \
           \"order-clauses\": [{\"column\": \"totalDuration\", \"order\": \"asc\"}]}" \
    > ${TEMPFILE}

tar tzvf ${TEMPFILE} # See download content
# tar xzvf ${TEMPFILE} # Unpack / extract download content
/bin/rm --force ${TEMPFILE}
```
