db.createUser({
  user: "reportsdev",
  pwd: "reportsdevpw",
  roles: [
    { role: "read", db: "query_db_DEV" },
    { role: "readWrite", db: "reports_state_DEV" }
  ]
});

// Create indexes for reports module

db = db.getSiblingDB('reports_state_DEV');

db.notification_queue.createIndex(
  {"status": 1, "user_id": 1},
  {name: "idx_status_user_id"}
);

print("Created indexes for reports module");
