db.createUser({
  user: "anonymizerdev",
  pwd: "anonymizerdevpw",
  roles: [
    { role: "read", db: "query_db_DEV" },
    { role: "readWrite", db: "anonymizer_state_DEV" }
  ]
});
