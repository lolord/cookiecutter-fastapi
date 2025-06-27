from datetime import datetime

from {{cookiecutter.project_name}}.db import db

db.get_collection("user").update_one(
    {"email": "admin@admin.com"},
    {
        "$set": {
            "c_at": datetime.now(),
            "deleted": 0,
            "enabled": True,
            "expire_at": None,
            "hashed_password": "$2b$12$UJRVKRUwTNwlrilgNcoCKOsZso4M9yLJNp7QS3.hmQQwbX9VUjU6u",
            "nickname": "admin",
            "permissions": [],
            "roles": ["admin"],
            "u_at": datetime.now(),
        }
    },
    upsert=True,
)

db.get_collection("permission").update_one(
    {"name": "admin"},
    {
        "$set": {
            "c_at": datetime.now(),
            "description": "admin permission",
            "enabled": True,
        }
    },
    upsert=True,
)
