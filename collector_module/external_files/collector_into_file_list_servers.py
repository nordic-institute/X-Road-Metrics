#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Python script to receive list of security servers available from CENTRAL_SERVER global configuration
# Name/IP of Central server given as first attribute sys.argv[1]
#
# NB! Global configuration signature is not checked. Use this program at your own risk.

import sys
import re
import requests
import xml.etree.ElementTree as ET

if len(sys.argv) != 2 or sys.argv[1] in ("-h", "-help", "--help"):
    print ("Usage: ${0} <central_server_name>\nThe Name/IP of Central server can be found in configuration anchor.")
    exit(0)

# Name/IP of Central server
CENTRAL_SERVER=sys.argv[1]

# Method to access Central server
CENTRAL_SERVER_METHOD="http"

# Timeout for requests
CENTRAL_SERVER_TIMEOUT=10.0

# Downloading shared-params.xml
try:
    globalConf = requests.get(CENTRAL_SERVER_METHOD + "://" + CENTRAL_SERVER + "/internalconf", timeout=CENTRAL_SERVER_TIMEOUT)
    globalConf.raise_for_status()
    # NB! re.search global configuration regex might be changed according version naming or other future naming conventions
    s = re.search("Content-location: (/V\d+/\d+/shared-params.xml)", globalConf.content)
    sharedParams = requests.get(CENTRAL_SERVER_METHOD + "://" + CENTRAL_SERVER + s.group(1), timeout=CENTRAL_SERVER_TIMEOUT)
    sharedParams.raise_for_status()
except requests.exceptions.RequestException:
    exit(0)

try:
    root = ET.fromstring(sharedParams.content)
    instance = root.find("./instanceIdentifier").text
    for server in root.findall("./securityServer"):
        ownerId = server.find("./owner").text
        owner = root.find("./member[@id='"+ownerId+"']")
        memberClass = owner.find("./memberClass/code").text
        memberCode = owner.find("./memberCode").text
        serverCode = server.find("./serverCode").text
        address = server.find("./address").text
        print (instance + "/" + memberClass + "/" + memberCode + "/" + serverCode + "/" + address)
except Exception:
    exit(0)


