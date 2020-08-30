#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Python script to collect operational monitoring data from given list of security servers
# Local security server SECURITY_SERVER_URL to be used to go through
# Threaded queries (THREAD_COUNT) in use
# Result files in directory LOG_PATH, rotated with max size LOG_MAX_SIZE
# Maximum amount of rotated logs to keep is LOG_BACKUP_COUNT
# Status file to keep nextRecordsFrom values is NEXT_RECORDS_FILE
#
# NB! Global configuration signature is not checked. Use this program at your own risk

import sys
import re
import requests
import uuid
import time
import zlib
import json
import Queue
import threading
import datetime
import os
import logging
from logging.handlers import RotatingFileHandler


###########################
# Configurable parameters #
###########################

# X-Road instance (Sample: XTEE-CI-XM, ee-dev, ee-test, EE)
INSTANCE = "EE"

# Security server IP or Name used by Central monitoring
SECURITY_SERVER = "#NA"

# Method to access Security server
SECURITY_SERVER_METHOD = "http"

SECURITY_SERVER_URL = '{0}://{1}'.format(SECURITY_SERVER_METHOD, SECURITY_SERVER)

# Central monitoring subsystem/member (as defined in global configuration)
#
# Message header of Instance Monitoring Client
# MEMBERCLASS is in {GOV, COM, NGO, NEE}
# Sample: MEMBERCLASS = "GOV"
MEMBERCLASS = "GOV"

# MEMBERCODE is registry code of institution
# Sample: MEMBERCODE = "70006317" # RIA, Riigi Infosüsteemi Amet, State Information Agency
MEMBERCODE = "70006317"

# SUBSYSTEMCODE is X-Road subsystem code, to be registered in RIHA, www.riha.ee
# Sample: SUBSYSTEMCODE = "monitoring"
SUBSYSTEMCODE = "monitoring"

# Monitoring client header, must match with X-Road header protocol and SECURITY_SERVER_URL configuration
MONITORING_CLIENT = """        <xrd:client id:objectType="SUBSYSTEM">
            <id:xRoadInstance>{0}</id:xRoadInstance>
            <id:memberClass>{1}</id:memberClass>
            <id:memberCode>{2}</id:memberCode>
            <id:subsystemCode>{3}</id:subsystemCode>
        </xrd:client>
""".format(INSTANCE, MEMBERCLASS, MEMBERCODE, SUBSYSTEMCODE)

# Debug levels: 0 = Errors only; 1 = Simple debug; 2 = Detailed debug
# Used only for internal logging. Does not match with logger.setLevel(logging.${LEVEL})
DEBUG=1

# Timeout for http requests
SECURITY_SERVER_TIMEOUT=10.0

# How many threads to use for data quering
THREAD_COUNT=4

# File for saving nextRecordsFrom values
NEXT_RECORDS_FILE="nextRecordsFrom.json"

# Amount of history to ask in the first time (in seconds)
# 1 min = 60 sec
# 1h = 60 min = 3600 sec
# RECORDS_FROM_OFFSET=3600
# 1 day = 24h = 86400 seconds
# RECORDS_FROM_OFFSET=86400
# 1 week = 7 days = 604800 seconds
# RECORDS_FROM_OFFSET=604800
# 1 month = 30 days = 18144000 seconds
# RECORDS_FROM_OFFSET=18144000
# 1 month = 31 days = 18748800 seconds
RECORDS_FROM_OFFSET=18748800

# Offset for the records_to parameter (gets records only up to "current time" - RECORDS_TO_OFFSET)
# Set this value to higher than default records-available-timestamp-offset-seconds=60
# Must be smaller than RECORDS_FROM_OFFSET
RECORDS_TO_OFFSET=100

# Repeat query to fetch additional data only if server has returned at least as much records
# By default servers should return 10000 records, so this value should be smaller
REPEAT_MIN_RECORDS=50

# How many times to repeat query if server has more records ("nextRecordsFrom" is returned by previous query)
# Set to 0 to disable query repeating.
# If this value is too low and script is executed rarely then some data may be lost
REPEAT_LIMIT=100

# Path to the logs. Leave empty for current directory or add path with "/" at the end
LOG_PATH = "./"
# We do use subdirectories in form of YYYY/MM/DD/ under LOG_PATH
now = datetime.datetime.now()
LOG_PATH = LOG_PATH + "/" + '{:04d}'.format(now.year) + "/" + '{:02d}'.format(now.month) + "/" + '{:02d}'.format(now.day) + "/"

if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

# Maximum log size (in bytes) before log rotation
# 10000000 ~ 10Mb
# 100000000 ~ 100Mb
LOG_MAX_SIZE = 100000000

# Maximum amount of rotated logs to keep. Setting to 0 will disable log rotation
LOG_BACKUP_COUNT = 100

##################################
# End of configurable parameters #
##################################

# Main function that queries data and saves to the logs
def process_data(threadName, serverData):
    # Example "server" values:
    # XTEE-CI/GOV/00000000/00000000_1/xtee8.ci.kit
    # XTEE-CI/GOV/00000001/00000001_1/xtee9.ci.kit
    # XTEE-CI/COM/00000002/00000002_1/xtee10.ci.kit
    # Server name part is "greedy" match to allow server names to have "/" character
    m = re.match("^(.+?)/(.+?)/(.+?)/(.+)/(.+?)$", serverData['server'])

    if m is None or m.lastindex != 5:
        sys.stderr.write(threadName + " Incorrect server string: " + serverData['server'] + "\n")
        return

    host_name = re.sub("[^0-9a-zA-Z\.-]+", '.', m.group(0))

    if DEBUG: print (threadName + ": " + host_name + ": " + "Processing server")

    if m.group(0) in nextRecordsFrom.keys():
        recordsFrom = nextRecordsFrom[m.group(0)]
        if DEBUG: print (threadName + ": " + host_name + ": " + "Read nextRecordsFrom")
    else:
        recordsFrom = str(int(time.time()) - RECORDS_FROM_OFFSET)
        if DEBUG: print (threadName + ": " + host_name + ": " + "Using defaults for recordsFrom")

    recordsTo = str(int(time.time()) - RECORDS_TO_OFFSET)

    if DEBUG: print (threadName + ": " + host_name + ": " + "Debug: recordsFrom=" + recordsFrom + "; recordsTo=" + recordsTo)

    body = """<SOAP-ENV:Envelope
       xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
       xmlns:id="http://x-road.eu/xsd/identifiers"
       xmlns:xrd="http://x-road.eu/xsd/xroad.xsd"
       xmlns:om="http://x-road.eu/xsd/op-monitoring.xsd">
    <SOAP-ENV:Header>
""" + MONITORING_CLIENT + """        <xrd:service id:objectType="SERVICE">
            <id:xRoadInstance>""" + m.group(1) + """</id:xRoadInstance>
            <id:memberClass>""" + m.group(2) + """</id:memberClass>
            <id:memberCode>""" + m.group(3) + """</id:memberCode>
            <id:serviceCode>getSecurityServerOperationalData</id:serviceCode>
        </xrd:service>
        <xrd:securityServer id:objectType="SERVER">
            <id:xRoadInstance>""" + m.group(1) + """</id:xRoadInstance>
            <id:memberClass>""" + m.group(2) + """</id:memberClass>
            <id:memberCode>""" + m.group(3) + """</id:memberCode>
            <id:serverCode>""" + m.group(4) + """</id:serverCode>
        </xrd:securityServer>
        <xrd:id>""" + str(uuid.uuid4()) + """</xrd:id>
        <xrd:protocolVersion>4.0</xrd:protocolVersion>
    </SOAP-ENV:Header>
    <SOAP-ENV:Body>
        <om:getSecurityServerOperationalData>
            <om:searchCriteria>
                <om:recordsFrom>""" + recordsFrom + """</om:recordsFrom>
                <om:recordsTo>""" + recordsTo + """</om:recordsTo>
            </om:searchCriteria>
        </om:getSecurityServerOperationalData>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""

    headers = {"Content-type": "text/xml;charset=UTF-8"}

    try:
        response = requests.post(SECURITY_SERVER_URL, data=body, headers=headers, timeout=SECURITY_SERVER_TIMEOUT)
        # if DEBUG > 1: print(threadName + ": " + host_name + ": " + "Response " + response.content)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        sys.stderr.write(threadName + ": " + host_name + ": " + "Cannot get response for: " + m.group(0) + "\n")
        # sys.stderr.write(threadName + ": " + host_name + ": " + "Response exception: " + response.content + "\n")
        return

    try:
        # Finding attachment
        resp_search = re.search("content-id: <operational-monitoring-data.json.gz>\r\n\r\n(.+)\r\n--xroad", response.content, re.DOTALL)
        data = json.loads(zlib.decompress(resp_search.group(1), zlib.MAX_WBITS|16))
        records=data["records"]
    except Exception:
        sys.stderr.write(threadName + ": " + host_name + ": " + "Cannot parse response attachment of: " + m.group(0) + "\n")
        sys.stderr.write(threadName + ": " + host_name + ": " + "Parse exception: " + response.content + "\n")
        return

    # Writing to log files
    if len(records):
        if DEBUG: print (threadName + ": " + host_name + ": " + "Appending " + str(len(records)) + " lines to log file")
        # TODO: host_name produces hierarchical logger. Can it be a problem?
        logger = logging.getLogger(host_name)
        logger.setLevel(logging.INFO)
        # Adding handler only if this is not a repeated query to the host
        if REPEAT_LIMIT == serverData['repeats']:
            handler = RotatingFileHandler(LOG_PATH + host_name + ".log", maxBytes=LOG_MAX_SIZE, backupCount=LOG_BACKUP_COUNT)
            logger.addHandler(handler)
        for record in records:
            logger.info(json.dumps(record, separators=(',', ':')))
            # if DEBUG > 1: print (threadName + ": " + host_name + ": " + "  added record: " + record["messageId"])
            # if DEBUG > 1: print (threadName + ": " + host_name + ": " + "  added record: " + str(record.get("messageId", None)))
            if DEBUG > 1: print (threadName + ": " + host_name + ": " + "  added record: " + \
                "messageId: " + str(record.get("messageId", None)) + " xRequestId: " + str(record.get("xRequestId", None)))
        # Removing handler to avoid duplicate handlers if query to this host is repeated.
        #logger.removeHandler(handler)
    elif DEBUG: print (threadName + ": " + host_name + ": " + "No data found to append to log file")

    # Update nextRecordsFrom value
    resp_search = re.search("<om:nextRecordsFrom>(\d+)</om:nextRecordsFrom>", response.content)
    if resp_search:
        # Locking nextRecordsFrom
        nextRecordsLock.acquire()
        nextRecordsFrom[m.group(0)] = resp_search.group(1)
        if DEBUG: print (threadName + ": " + host_name + ": " + "Using nextRecordsFrom from response: " + nextRecordsFrom[m.group(0)])
        nextRecordsLock.release()

        # Deciding if we should repeat query and fetch additional data
        if len(records) < REPEAT_MIN_RECORDS:
            sys.stderr.write(threadName + ": " + host_name + ": " + "Not enough data received (" + str(len(records)) + ") to repeat query to server " + m.group(0) + "\n")
        elif serverData['repeats']:
            serverData['repeats'] -= 1
            # Locking workQueue
            queueLock.acquire()
            workQueue.put(serverData)
            queueLock.release()
            if DEBUG: print (threadName + ": " + host_name + ": " + "Adding to queue the request (nr " + str(REPEAT_LIMIT - serverData['repeats']) + ") to fetch additional data from server " + m.group(0))
        else:
            sys.stderr.write(threadName + ": " + host_name + ": " + "Maximum repeats reached for server " + m.group(0) + "\n")
    else:
        # Locking nextRecordsFrom
        nextRecordsLock.acquire()
        nextRecordsFrom[m.group(0)] = str(int(recordsTo) + 1)
        if DEBUG: print (threadName + ": " + host_name + ": " + "Using recordsTo + 1 for nextRecordsFrom: " + nextRecordsFrom[m.group(0)])
        nextRecordsLock.release()

# Class for handling threads
class myThread (threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    def run(self):
        if DEBUG: print ("Starting " + self.name)

        global workingThreads
        while not exitFlag:
            # Locking workQueue
            queueLock.acquire()
            if not workQueue.empty():
                data = self.q.get()
                queueLock.release()
                # Locking workingThreads - thread started working
                workingThreadsLock.acquire()
                workingThreads += 1
                workingThreadsLock.release()
                # Calling main processing function
                process_data(self.name, data)
                # Locking workingThreads - thread finished working
                workingThreadsLock.acquire()
                workingThreads -= 1
                workingThreadsLock.release()
            else:
                queueLock.release()
            time.sleep(0.1)

        if DEBUG: print ("Exiting " + self.name)


# Used to signal threades to exit. 0 = continue; 1 = exit
exitFlag = 0

# Read nextRecordsFrom values
try:
    with open(NEXT_RECORDS_FILE) as jsonData:
        nextRecordsFrom = json.load(jsonData)
except IOError:
    nextRecordsFrom = {}

# Lock for nextRecordsFrom
nextRecordsLock = threading.Lock()

# Working queue (list of servers to load the data from)
workQueue = Queue.Queue()

# Lock of workQueue
queueLock = threading.Lock()

# List of threads
threads = []

# Amount of threads that are working at this moment
workingThreads = 0

# Lock for workingThreads
workingThreadsLock = threading.Lock()

# Fill workqueue with stdin values
for line in sys.stdin:
    data = {'server': line, 'repeats': REPEAT_LIMIT}
    workQueue.put(data)

# Create and start new threads
for threadID in range(1, THREAD_COUNT + 1):
    thread = myThread(threadID, "Thread-"+str(threadID), workQueue)
    thread.start()
    threads.append(thread)

# Wait for queue to empty and all threads to go idle
while not (workQueue.empty() and workingThreads == 0):
    time.sleep(0.1)

# Notify threads it's time to exit
exitFlag = 1

# Wait for all threads to complete
for t in threads:
    t.join()

# Save nextRecordsFrom values
with open(NEXT_RECORDS_FILE, 'w') as jsonData:
    json.dump(nextRecordsFrom, jsonData, sort_keys=True, indent=4)

if DEBUG: print ("Exiting Main Thread")
