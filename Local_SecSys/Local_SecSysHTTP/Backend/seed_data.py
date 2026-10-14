"""Insert demo data. Run from this file's directory: python seed_data.py"""
from pathlib import Path
import bcrypt
from db import doors_col, users_col
from schemas import door_schema, user_schema, face_schema

BASE_DIR = Path(__file__).resolve().parent

def load_image(filename):
    with (BASE_DIR / "faces" / filename).open("rb") as image_file:
        return image_file.read()

# Demo-only reset: these two collections are cleared before reseeding.
doors_col.delete_many({})
users_col.delete_many({})
doors_col.insert_one(door_schema("Door1", ["manish"]))
pin_hash = bcrypt.hashpw(b"1234", bcrypt.gensalt())
faces = [face_schema(load_image("bob1.jpeg")), face_schema(load_image("bob2.jpeg"))]
users_col.insert_one(user_schema("manish", "Door1", pin_hash, faces))
print("Demo data inserted: Door1 / user manish / PIN 1234")
