db.createUser({
  user: "correctordev",
  pwd: "correctordevpw",
  roles: [
    { role: "readWrite", db: "query_db_DEV" }
  ]
});

// Create indexes for corrector module (clean_data collection)

db = db.getSiblingDB('query_db_DEV');

db.clean_data.createIndex(
  {"xRequestId": 1},
  {name: "idx_xRequestId"}
);

db.clean_data.createIndex(
  {"correctorTime": 1},
  {name: "idx_correctorTime"}
);

db.clean_data.createIndex(
  {"correctorStatus": 1, "client.requestInTs": 1},
  {name: "idx_correctorStatus_client_requestInTs"}
);

db.clean_data.createIndex(
  {"correctorStatus": 1, "producer.requestInTs": 1},
  {name: "idx_correctorStatus_producer_requestInTs"}
);

db.clean_data.createIndex(
  {"correctorStatus": 1, "xRequestId": 1},
  {name: "idx_correctorStatus_xRequestId"}
);

db.clean_data.createIndex(
  {"client.xRequestId": 1},
  {name: "idx_client_xRequestId"}
);

db.clean_data.createIndex(
  {"client.requestInTs": 1},
  {name: "idx_client_requestInTs"}
);

db.clean_data.createIndex(
  {"client.serviceCode": 1},
  {name: "idx_client_serviceCode"}
);

db.clean_data.createIndex(
  {"producer.requestInTs": 1},
  {name: "idx_producer_requestInTs"}
);

db.clean_data.createIndex(
  {"producer.serviceCode": 1},
  {name: "idx_producer_serviceCode"}
);

db.clean_data.createIndex(
  {"producer.xRequestId": 1},
  {name: "idx_producer_xRequestId"}
);

// Compound indexes for reports module queries
db.clean_data.createIndex(
  {"client.clientMemberCode": 1, "client.clientSubsystemCode": 1, "client.requestInTs": 1},
  {name: "idx_client_client"}
);

db.clean_data.createIndex(
  {"client.serviceMemberCode": 1, "client.serviceSubsystemCode": 1, "client.requestInTs": 1},
  {name: "idx_client_service"}
);

db.clean_data.createIndex(
  {"producer.clientMemberCode": 1, "producer.clientSubsystemCode": 1, "producer.requestInTs": 1},
  {name: "idx_producer_client"}
);

db.clean_data.createIndex(
  {"producer.serviceMemberCode": 1, "producer.serviceSubsystemCode": 1, "producer.requestInTs": 1},
  {name: "idx_producer_service"}
);

print("Created indexes for corrector module");
