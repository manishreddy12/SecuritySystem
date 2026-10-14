from bson import ObjectId
from bson.binary import Binary
from datetime import datetime

def door_schema(doorName, allowed_users):
    return {
        "doorName": doorName,
        "allowed_users": allowed_users
    }


def face_schema(image_bytes):
    return {
        "_id": ObjectId(),
        "image": Binary(image_bytes)
    }


def user_schema(username, doorName, pin_hash, faces=None):
    return {
        "username": username,
        "doorName": doorName,
        "pin_hash": pin_hash,
        "faces": faces or []                  
    }

def uploaded_face_schema(image_bytes):
    return {
        "_id": ObjectId(),
        "image": Binary(image_bytes),
        "created_at": datetime.utcnow()
    }

def validate_user(doc):
    required = ["username", "doorName", "pin_hash", "faces"]
    return all(k in doc for k in required)

def validate_face(face):
    return "_id" in face and "image" in face
