db.createUser({
  user: "reportsdev",
  pwd: "reportsdevpw",
  roles: [
    { role: "readWrite", db: "query_db_DEV" },
    { role: "readWrite", db: "collector_state_DEV" }
  ]
});
