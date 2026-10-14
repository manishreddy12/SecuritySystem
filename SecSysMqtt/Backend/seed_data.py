from db import doors_col, users_col
import bcrypt
from schemas import door_schema, user_schema, face_schema

def load_image(path):
    with open(path, "rb") as f:
        return f.read()

# Clear old data (dev only)
doors_col.delete_many({})
users_col.delete_many({})

# Create Door
doors_col.insert_one(
    door_schema("Door1", ["manish"])
)

# Create User
pin = "1234"
pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt())

faces = [
    face_schema(load_image("faces/bob1.jpeg")),
    face_schema(load_image("faces/bob2.jpeg"))
]

users_col.insert_one(
    user_schema("manish", "Door1", pin_hash, faces)
)

print("✅ Seed data inserted using schemas")



# from db import doors_col, users_col
# from pymongo import MongoClient
# import bcrypt
# from bson.binary import Binary

# def load_image(path):
#     with open(path, "rb") as f:
#         return Binary(f.read())

# # Create Door
# doors_col.insert_one({
#     "doorName": "Door1",
#     "allowed_users": ["manish"]
# })

# # Create User
# pin = "1234"
# pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt())

# user = {
#     "username": "manish",
#     "doorName": "Door1",
#     "pin_hash": pin_hash,
#     "faces": [
#         {"image": load_image("faces/bob1.jpeg")},
#         {"image": load_image("faces/bob2.jpeg")}
#     ]
# }

# users_col.insert_one(user)

# print("✅ Seed data inserted successfully")
