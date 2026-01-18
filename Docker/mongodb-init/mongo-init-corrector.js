db.createUser({
  user: "correctordev",
  pwd: "correctordevpw",
  roles: [
    { role: "readWrite", db: "query_db_DEV" }
  ]
});
