from pathlib import Path
import bcrypt
from db import doors_col, users_col
from schemas import door_schema, user_schema, face_schema

BASE_DIR = Path(__file__).resolve().parent

def load_image(filename):
    with (BASE_DIR / "faces" / filename).open("rb") as f:
        return f.read()

# Clear old demo data
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
    face_schema(load_image("bob1.jpeg")),
    face_schema(load_image("bob2.jpeg"))
]

users_col.insert_one(
    user_schema("manish", "Door1", pin_hash, faces)
)

print("Demo data inserted: Door1 / user manish / PIN 1234")
