import logging
from logging.handlers import WatchedFileHandler
import os

# --------------------------------------------------------
# General settings
# --------------------------------------------------------
MODULE = "analyzer"
APPDIR = "/srv/app"
INSTANCE = "sample"

# --------------------------------------------------------
# MongoDB settings
# --------------------------------------------------------
MDB_USER = '{0}_{1}'.format(MODULE, INSTANCE)
MDB_PWD = "#NA"
MDB_SERVER = "#NA"
MONGODB_SUFFIX = '{0}'.format(INSTANCE)
MONGODB_URI = "mongodb://{0}:{1}@{2}/auth_db".format(MDB_USER, MDB_PWD, MDB_SERVER)

MONGODB_QD = 'query_db_{0}'.format(INSTANCE)
MONGODB_AD = 'analyzer_database_{0}'.format(INSTANCE)

# --------------------------------------------------------
# Configure logger
# --------------------------------------------------------
# Ensure match with external logrotate settings
LOGGER_NAME = '{0}'.format(MODULE)
LOGGER_PATH = '{0}/{1}/logs/'.format(APPDIR, INSTANCE)
logger = logging.getLogger(LOGGER_NAME)

# INFO - logs INFO & WARNING & ERROR
# WARNING - logs WARNING & ERROR
# ERROR - logs ERROR
logger.setLevel(logging.INFO)
log_file_name = 'log_{0}_{1}.json'.format(LOGGER_NAME, INSTANCE)
log_file = os.path.join(LOGGER_PATH, log_file_name)
formatter = logging.Formatter("%(message)s")
file_handler = WatchedFileHandler(log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# --------------------------------------------------------
# Configure heartbeat
# --------------------------------------------------------
# Ensure match with external application monitoring settings
HEARTBEAT_PATH = '{0}/{1}/heartbeat/'.format(APPDIR, INSTANCE)
HEARTBEAT_FILE = 'heartbeat_{0}_{1}.json'.format(MODULE, INSTANCE)
