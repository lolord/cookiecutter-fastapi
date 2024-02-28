// Create user
dbAdmin = db.getSiblingDB("admin");
dbAdmin.createUser({
  user: "mongo",
  pwd: "123456",
  roles: [{ role: "userAdminAnyDatabase", db: "admin" }],
  mechanisms: ["SCRAM-SHA-1"],
});

// Authenticate user
dbAdmin.auth({
  user: "mongo",
  pwd: "123456",
  mechanisms: ["SCRAM-SHA-1"],
  digestPassword: true,
});

// Create DB and collection
db = new Mongo().getDB("{{cookiecutter.project_name}}");
db.createCollection("user", { capped: false });
db.createCollection("permission", { capped: false });


db.user.insert({
  "c_at": ISODate(),
  "deleted": 0,
  "email": "admin@admin.com",
  "enabled": true,
  "expire_at": null,
  "hashed_password": "$2b$12$UJRVKRUwTNwlrilgNcoCKOsZso4M9yLJNp7QS3.hmQQwbX9VUjU6u",
  "nickname": "admin",
  "permissions": [],
  "roles": [
    "admin"
  ],
  "u_at": ISODate()
});


db.createCollection("permission", { capped: false });

db.permission.insert({
  "c_at": ISODate(),
  "name": "admin",
  "description": "admin permission",
  "enabled": true,
});
