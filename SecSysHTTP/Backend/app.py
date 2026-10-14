from io import BytesIO

import bcrypt
import requests
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError

from config import FACE_RECOG_URL, MAX_CONTENT_LENGTH, REQUEST_TIMEOUT
from db import doors_col, users_col, faces_col
from schemas import uploaded_face_schema

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app)


def error(message, status=400, **extra):
    return jsonify({"error": message, **extra}), status


def image_is_valid(image_bytes):
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def image_file(image_bytes, filename):
    """Return a requests-compatible multipart image tuple."""
    return (filename, BytesIO(image_bytes), "image/jpeg")


@app.get("/health")
def health():
    try:
        doors_col.database.client.admin.command("ping")
        return jsonify({"status": "ok", "database": "reachable"})
    except Exception:
        app.logger.exception("MongoDB health check failed")
        return error("Database unavailable", 503)


@app.post("/ring-doorbell")
def ring_doorbell():
    data = request.get_json(silent=True) or {}
    door_name = data.get("doorName", "").strip()
    if not door_name:
        return error("doorName is required")

    try:
        door = doors_col.find_one({"doorName": door_name})
    except Exception:
        app.logger.exception("Door lookup failed")
        return error("Database unavailable", 503)

    if not door:
        return error("Door not found", 404)
    return jsonify({"doorId": str(door["_id"]), "doorName": door_name})


@app.post("/face-upload")
def face_upload():
    uploaded = request.files.get("face")
    if uploaded is None:
        return error("Image file field 'face' is required")
    image_bytes = uploaded.read()
    if not image_bytes:
        return error("Uploaded image is empty")
    if not image_is_valid(image_bytes):
        return error("Uploaded file is not a valid image")

    try:
        face_doc = uploaded_face_schema(image_bytes)
        faces_col.insert_one(face_doc)
        return jsonify({"success": True, "face_id": str(face_doc["_id"])}), 201
    except Exception:
        app.logger.exception("Face upload failed")
        return error("Could not save uploaded face", 500)


@app.post("/verifyFace")
def verify_face():
    data = request.get_json(silent=True) or {}
    door_name = data.get("doorName", "").strip()
    face_id = data.get("face_id", "").strip()
    if not door_name or not face_id:
        return error("doorName and face_id are required")
    try:
        face_object_id = ObjectId(face_id)
    except (InvalidId, TypeError):
        return error("face_id is invalid")

    try:
        door = doors_col.find_one({"doorName": door_name})
        if not door:
            return jsonify({"matched": False, "error": "Invalid door"}), 404

        uploaded_face = faces_col.find_one({"_id": face_object_id})
        if not uploaded_face:
            return jsonify({"matched": False, "error": "Face not found"}), 404

        uploaded_image = bytes(uploaded_face["image"])
        users = list(users_col.find({"doorName": door_name}))
    except Exception:
        app.logger.exception("Database error during face verification")
        return error("Database unavailable", 503)

    try:
        for user in users:
            for stored_face in user.get("faces", []):
                stored_image = bytes(stored_face["image"])
                files = {
                    "img1": image_file(stored_image, "stored.jpg"),
                    "img2": image_file(uploaded_image, "uploaded.jpg"),
                }
                response = requests.post(FACE_RECOG_URL, files=files, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                result = response.json()
                if result.get("verified"):
                    return jsonify({"matched": True, "username": user["username"]})
        return jsonify({"matched": False})
    except requests.Timeout:
        app.logger.exception("Face recognition service timed out")
        return error("Face recognition timed out", 504, matched=False)
    except requests.RequestException:
        app.logger.exception("Face recognition service request failed")
        return error("Face recognition service unavailable", 502, matched=False)
    except (ValueError, KeyError):
        app.logger.exception("Invalid response from face recognition service")
        return error("Invalid face recognition response", 502, matched=False)


@app.post("/verifyPin")
def verify_pin():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    door_name = data.get("doorName", "").strip()
    plain_pin = data.get("plainPin", "")
    if not username or not door_name or not isinstance(plain_pin, str) or not plain_pin:
        return error("username, doorName, and plainPin are required")

    try:
        user = users_col.find_one({"username": username, "doorName": door_name})
    except Exception:
        app.logger.exception("PIN lookup failed")
        return error("Database unavailable", 503)

    if not user:
        return jsonify({"success": False, "error": "User not found for this door"}), 404
    try:
        valid = bcrypt.checkpw(plain_pin.encode("utf-8"), bytes(user["pin_hash"]))
    except (ValueError, TypeError, KeyError):
        app.logger.exception("Stored PIN hash is invalid")
        return error("Stored PIN hash is invalid", 500)
    return jsonify({"success": bool(valid)})


@app.errorhandler(413)
def file_too_large(_exc):
    return error("File too large; maximum upload size is 10 MB", 413)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
