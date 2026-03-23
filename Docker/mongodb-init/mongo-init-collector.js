db.createUser({
  user: "collectordev",
  pwd: "collectordevpw",
  roles: [
    { role: "readWrite", db: "query_db_DEV" },
    { role: "readWrite", db: "collector_state_DEV" }
  ]
});

// Create indexes for collector module

db = db.getSiblingDB('query_db_DEV');

db.raw_messages.createIndex(
  {"requestInTs": 1},
  {name: "idx_requestInTs"}
);

db.raw_messages.createIndex(
  {"corrected": 1, "requestInTs": 1},
  {name: "idx_corrected_requestInTs"}
);

db = db.getSiblingDB('collector_state_DEV');

db.server_list.createIndex(
  {"timestamp": 1},
  {name: "idx_timestamp"}
);

print("Created indexes for collector module");
