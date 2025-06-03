db.createUser({
  user: "opendatacollectordev",
  pwd: "opendatacollectordevpw",
  roles: [
    { role: "readWrite", db: "query_db_DEV" },
    { role: "readWrite", db: "collector_state_DEV" }
  ]
});
