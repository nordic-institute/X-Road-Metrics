db.createUser({
  user: "reportsdev",
  pwd: "reportsdevpw",
  roles: [
    { role: "read", db: "query_db_DEV" },
    { role: "readWrite", db: "reports_state_DEV" }
  ]
});
