#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#

# --------------------------------------------------------
# General settings
# --------------------------------------------------------
MODULE = "archiver"
# X-Road instances in Estonia: ee-dev, ee-test, EE
INSTANCE = "sample"
APPDIR = '/opt/archive'

# --------------------------------------------------------
# MongoDB settings
# --------------------------------------------------------
MONGODB_SERVER = "#NA"
MONGODB_PORT = "27017"
MONGODB_USER = '{0}_{1}'.format(MODULE, INSTANCE)
MONGODB_PWD = "#NA"

# MONGODB_QUERY_DB = "query_db_sample"
MONGODB_QUERY_DB = 'query_db_{0}'.format(INSTANCE)
# MONGODB_AUTH_DB = "auth_db" # or MONGODB_AUTH_DB = "admin"
MONGODB_AUTH_DB = "auth_db"

# --------------------------------------------------------
# Module settings
# --------------------------------------------------------
# Amount of operational monitoring clean_data logs to be archived (in days).
X_DAYS_AGO = 180 # in days

# Minimum queries to be archived, default
MINIMUM_TO_ARCHIVE = 100000
# Total queries to be archived, default
TOTAL_TO_ARCHIVE = 150000

# Raw messages archive directory
# RAW_MESSAGES_ARCHIVE_DIR = "/srv/archive/sample"
RAW_MESSAGES_ARCHIVE_DIR = '/srv/archive/{0}'.format(INSTANCE)

# Clean data archive directory
# CLEAN_DATA_ARCHIVE_DIR = "/srv/archive/sample"
CLEAN_DATA_ARCHIVE_DIR = '/srv/archive/{0}'.format(INSTANCE)

# --------------------------------------------------------
# Configure logger
# --------------------------------------------------------
# Ensure match with external logrotate settings
# LOGGER_NAME = "archiver"
LOGGER_NAME = '{0}'.format(MODULE)
# LOGGER_PATH = "/opt/archive/sample/logs"
LOGGER_PATH = '{0}/{1}/logs'.format(APPDIR, INSTANCE)
# LOGGER_FILE = "log_archiver_sample.json"
LOGGER_FILE = 'log_{0}_{1}.json'.format(MODULE, INSTANCE)
# LOGGER_LEVEL = logging.DEBUG # Deprecated

# --------------------------------------------------------
# Configure heartbeat
# --------------------------------------------------------
# Ensure match with external application monitoring settings
# HEARTBEAT_PATH = "/opt/archive/archiver/sample/heartbeat"
HEARTBEAT_PATH = '{0}/{1}/heartbeat'.format(APPDIR, INSTANCE)
# HEARTBEAT_FILE = "heartbeat_archiver_sample.json"
HEARTBEAT_FILE = 'heartbeat_{0}_{1}.json'.format(MODULE, INSTANCE)

# --------------------------------------------------------
# End of settings
# --------------------------------------------------------
