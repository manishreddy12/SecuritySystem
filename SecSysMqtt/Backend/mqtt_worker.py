import json
import base64
import requests
import io
from PIL import Image
import paho.mqtt.client as mqtt
from db import doors_col, users_col
from config import MQTT_BROKER, MQTT_PORT, FACE_RECOG_URL
import bcrypt
from bson import ObjectId
from schemas import face_schema
import datetime
# def on_connect(client, userdata, flags, rc):
#     print("MQTT Worker connected")
#     client.subscribe("door/+/request")
#     client.subscribe("")

def on_connect(client, userdata, flags, rc):
    print("MQTT Worker connected")
    client.subscribe("door/+/request")
    client.subscribe("face/verify/request")
    client.subscribe("face/upload/request")
    client.subscribe("pin/verify/request")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = json.loads(msg.payload.decode())

    if topic == "door/ring/request":
        handle_ring(client, payload)

    elif topic == "face/verify/request":
        handle_face_verify(client, payload)

    elif topic == "pin/verify/request":
        handle_pin_verify(client, payload)

    elif topic == "face/upload/request":      # NEW
        handle_face_upload(client, payload)

def handle_ring(client, payload):
    doorName = payload["doorName"]
    req_id = payload["request_id"]

    door = doors_col.find_one({"doorName": doorName})
    if not door:
        resp = {"request_id": req_id, "error": "Door not found"}
    else:
        resp = {"request_id": req_id, "doorId": str(door["_id"])}

    client.publish("door/ring/response", json.dumps(resp))

def image_to_file(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG")
    buf.seek(0)
    return buf


from schemas import uploaded_face_schema
from db import faces_col

def handle_face_upload(client, payload):
    req_id = payload["request_id"]
    img_b64 = payload["image"]

    img_bytes = base64.b64decode(img_b64)
    face_doc = uploaded_face_schema(img_bytes)

    faces_col.insert_one(face_doc)

    client.publish("face/upload/response", json.dumps({
        "request_id": req_id,
        "success": True,
        "face_id": str(face_doc["_id"])
    }))


# def handle_face_upload(client, payload):
#     req_id = payload["request_id"]
#     username = payload["username"]
#     doorName = payload["doorName"]
#     img_b64 = payload["image"]

#     img_bytes = base64.b64decode(img_b64)

#     user = users_col.find_one({"username": username, "doorName": doorName})

#     if not user:
#         result = users_col.insert_one({
#             "username": username,
#             "doorName": doorName,
#             "faces": [{"image": img_bytes}]
#         })
#         face_id = str(result.inserted_id)   # fallback id
#     else:
#         face_obj = {"_id": ObjectId(), "image": img_bytes}
#         users_col.update_one(
#             {"_id": user["_id"]},
#             {"$push": {"faces": face_obj}}
#         )
#         face_id = str(face_obj["_id"])

#     client.publish("face/upload/response", json.dumps({
#         "request_id": req_id,
#         "success": True,
#         "face_id": face_id
#     }))

def handle_face_verify(client, payload):
    req_id = payload["request_id"]
    doorName = payload["doorName"]
    face_id = payload["face_id"]   # mongo id of uploaded face


    users = list(users_col.find({"doorName": doorName}))
    if not users:
        client.publish("face/verify/response", json.dumps({
            "request_id": req_id,
            "error": "Invalid door",
            "matched": False
        }))
        return

    # 1️⃣ Fetch uploaded image from faces collection
    uploaded_face = faces_col.find_one({"_id": ObjectId(face_id)})

    if not uploaded_face:
        client.publish("face/verify/response", json.dumps({
            "request_id": req_id,
            "matched": False,
            "error": "Face not found"
        }))
        return

    uploaded_img = Image.open(
        io.BytesIO(uploaded_face["image"])
    ).convert("RGB")

    # 2️⃣ Fetch all users for that door
    users = users_col.find({"doorName": doorName})

    # 3️⃣ Loop through all users & faces and verify
    for user in users:
        for face in user.get("faces", []):
            stored_img = Image.open(
                io.BytesIO(face["image"])
            ).convert("RGB")

            files = {
                "img1": (
                    "stored.jpg",
                    image_to_file(stored_img),
                    "image/jpeg"
                ),
                "img2": (
                    "uploaded.jpg",
                    image_to_file(uploaded_img),
                    "image/jpeg"
                )
            }

            r = requests.post(FACE_RECOG_URL, files=files)

            if r.status_code != 200:
                continue

            result = r.json()

            if result.get("verified"):
                client.publish("face/verify/response", json.dumps({
                    "request_id": req_id,
                    "matched": True,
                    "username": user["username"]
                }))
                return

    # 4️⃣ No match found
    client.publish("face/verify/response", json.dumps({
        "request_id": req_id,
        "matched": False
    }))




# def handle_face_verify(client, payload):
#     req_id = payload["request_id"]
#     doorName = payload["doorName"]
#     uploaded_img_b64 = payload["image"]

#     uploaded_img = Image.open(io.BytesIO(base64.b64decode(uploaded_img_b64)))

#     users = users_col.find({"doorName": doorName})

#     for user in users:
#         for face in user["faces"]:
#             stored_img = Image.open(io.BytesIO(face["image"]))

#             files = {
#                 "img1": image_to_file(stored_img),
#                 "img2": image_to_file(uploaded_img)
#             }

#             r = requests.post(FACE_RECOG_URL, files=files)
#             result = r.json()

#             if result.get("verified"):
#                 resp = {
#                     "request_id": req_id,
#                     "matched": True,
#                     "username": user["username"]
#                 }
#                 client.publish("face/verify/response", json.dumps(resp))
#                 return

#     client.publish("face/verify/response", json.dumps({
#         "request_id": req_id,
#         "matched": False
#     }))

def handle_pin_verify(client, payload):
    req_id = payload["request_id"]
    username = payload["username"]
    plain_pin = payload["plainPin"]
    doorName = payload["doorName"]

    user = users_col.find_one({"username": username, "doorName": doorName})
    if not user:
        resp = {
            "request_id": req_id,
            "success": False,
            "error": "Invalid door or user"
        }


    user = users_col.find_one({
        "username": username,
        "doorName": doorName
    })

    if not user:
        resp = {
            "request_id": req_id,
            "success": False,
            "error": "User not found for this door"
        }
    else:
        ok = bcrypt.checkpw(
            plain_pin.encode(),
            user["pin_hash"]
        )
        resp = {
            "request_id": req_id,
            "success": ok
        }

    client.publish("pin/verify/response", json.dumps(resp))


def image_to_file(img):
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_forever()
