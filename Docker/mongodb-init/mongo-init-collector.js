db.createUser({
  user: "collectordev",
  pwd: "collectordevpw",
  roles: [
    { role: "readWrite", db: "query_db_DEV" },
    { role: "readWrite", db: "collector_state_DEV" }
  ]
});
