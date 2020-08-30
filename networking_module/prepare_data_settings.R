# This is a Networking modules settings file. 
# Different settings file must be configured for each X-Road instance.

# The name of the X-Road instance.
instancename="sample"

# Time interval in days for which the data is queried.
interval=5

# Time buffer backward from the last date to enable data collection and correction.
buffer=10

# List of metaservices (services related to the X-road monitoring by the Information System Authority).
metaservices<-c("getWsdl", "listMethods", "allowedMethods", "getSecurityServerMetrics", "getSecurityServerOperationalData", "getSecurityServerHealthData")

# Open data PostgreSQL database credentials. 
host="#NA"
dbname="opendata_sample"
user="networking_sample"
port=5432
pwd="#NA"
