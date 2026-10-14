from bson import ObjectId
from bson.binary import Binary
from datetime import datetime


def door_schema(door_name, allowed_users):
    return {"doorName": door_name, "allowed_users": allowed_users}


def face_schema(image_bytes):
    return {"_id": ObjectId(), "image": Binary(image_bytes)}


def user_schema(username, door_name, pin_hash, faces=None):
    return {
        "username": username,
        "doorName": door_name,
        "pin_hash": pin_hash,
        "faces": faces or [],
    }


def uploaded_face_schema(image_bytes):
    return {
        "_id": ObjectId(),
        "image": Binary(image_bytes),
        "created_at": datetime.utcnow(),
    }
