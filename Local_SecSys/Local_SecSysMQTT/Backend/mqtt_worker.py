import json
import base64
import requests
import io
from PIL import Image
import paho.mqtt.client as mqtt
from db import doors_col, users_col, faces_col
from config import MQTT_BROKER, MQTT_PORT, FACE_RECOG_URL, REQUEST_TIMEOUT
import bcrypt
from bson import ObjectId
from schemas import uploaded_face_schema

def image_to_file(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG")
    buf.seek(0)
    return buf

def on_connect(client, userdata, flags, rc):
    print("MQTT Worker connected to broker.")
    client.subscribe("door/+/request")
    client.subscribe("face/verify/request")
    client.subscribe("face/upload/request")
    client.subscribe("pin/verify/request")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if topic == "door/ring/request":
            handle_ring(client, payload)
        elif topic == "face/verify/request":
            handle_face_verify(client, payload)
        elif topic == "pin/verify/request":
            handle_pin_verify(client, payload)
        elif topic == "face/upload/request":
            handle_face_upload(client, payload)
    except Exception as e:
        print(f"Error handling MQTT message on {msg.topic}: {e}")

def handle_ring(client, payload):
    doorName = payload.get("doorName", "")
    req_id = payload.get("request_id")

    door = doors_col.find_one({"doorName": doorName})
    if not door:
        resp = {"request_id": req_id, "error": "Door not found"}
    else:
        resp = {"request_id": req_id, "doorId": str(door["_id"]), "doorName": doorName}

    client.publish("door/ring/response", json.dumps(resp))

def handle_face_upload(client, payload):
    req_id = payload.get("request_id")
    img_b64 = payload.get("image", "")

    try:
        img_bytes = base64.b64decode(img_b64)
        face_doc = uploaded_face_schema(img_bytes)
        faces_col.insert_one(face_doc)

        client.publish("face/upload/response", json.dumps({
            "request_id": req_id,
            "success": True,
            "face_id": str(face_doc["_id"])
        }))
    except Exception as e:
        client.publish("face/upload/response", json.dumps({
            "request_id": req_id,
            "success": False,
            "error": str(e)
        }))

def handle_face_verify(client, payload):
    req_id = payload.get("request_id")
    doorName = payload.get("doorName", "")
    face_id = payload.get("face_id", "")

    try:
        face_obj_id = ObjectId(face_id)
    except Exception:
        client.publish("face/verify/response", json.dumps({
            "request_id": req_id,
            "matched": False,
            "error": "Invalid face ID format"
        }))
        return

    door = doors_col.find_one({"doorName": doorName})
    if not door:
        client.publish("face/verify/response", json.dumps({
            "request_id": req_id,
            "error": "Invalid door",
            "matched": False
        }))
        return

    uploaded_face = faces_col.find_one({"_id": face_obj_id})
    if not uploaded_face:
        client.publish("face/verify/response", json.dumps({
            "request_id": req_id,
            "matched": False,
            "error": "Face not found"
        }))
        return

    try:
        uploaded_img = Image.open(io.BytesIO(uploaded_face["image"])).convert("RGB")
        users = list(users_col.find({"doorName": doorName}))

        for user in users:
            for face in user.get("faces", []):
                stored_img = Image.open(io.BytesIO(face["image"])).convert("RGB")

                files = {
                    "img1": ("stored.jpg", image_to_file(stored_img), "image/jpeg"),
                    "img2": ("uploaded.jpg", image_to_file(uploaded_img), "image/jpeg")
                }

                try:
                    r = requests.post(FACE_RECOG_URL, files=files, timeout=REQUEST_TIMEOUT)
                    if r.status_code == 200:
                        result = r.json()
                        if result.get("verified"):
                            client.publish("face/verify/response", json.dumps({
                                "request_id": req_id,
                                "matched": True,
                                "username": user["username"]
                            }))
                            return
                except requests.RequestException as req_err:
                    print(f"Face recognition call error: {req_err}")
                    continue

        client.publish("face/verify/response", json.dumps({
            "request_id": req_id,
            "matched": False
        }))
    except Exception as e:
        client.publish("face/verify/response", json.dumps({
            "request_id": req_id,
            "matched": False,
            "error": str(e)
        }))

def handle_pin_verify(client, payload):
    req_id = payload.get("request_id")
    username = payload.get("username", "")
    plain_pin = payload.get("plainPin", "")
    doorName = payload.get("doorName", "")

    user = users_col.find_one({"username": username, "doorName": doorName})
    if not user:
        resp = {
            "request_id": req_id,
            "success": False,
            "error": "User not found for this door"
        }
    else:
        try:
            ok = bcrypt.checkpw(plain_pin.encode("utf-8"), bytes(user["pin_hash"]))
            resp = {
                "request_id": req_id,
                "success": bool(ok)
            }
        except Exception as e:
            resp = {
                "request_id": req_id,
                "success": False,
                "error": "PIN hash validation error"
            }

    client.publish("pin/verify/response", json.dumps(resp))

# Support both paho-mqtt v1 and v2
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message
print(f"Connecting MQTT worker to {MQTT_BROKER}:{MQTT_PORT} ...")
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_forever()
