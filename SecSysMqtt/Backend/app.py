from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import uuid, json, time
from config import MQTT_BROKER, MQTT_PORT
import base64
from flask_cors import CORS

# app = Flask(__name__)
app = Flask(__name__)
CORS(app)   # 👈 allow browser requests

responses = {}

mqtt_client = mqtt.Client()

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    responses[payload["request_id"]] = payload

mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe([
    ("door/ring/response", 0),
    ("face/verify/response", 0),
    ("pin/verify/response", 0),
    ("face/upload/response", 0),
])
mqtt_client.loop_start()

def wait_response(req_id, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        if req_id in responses:
            return responses.pop(req_id)
        time.sleep(0.05)
    return None

@app.route("/ring-doorbell", methods=["POST"])
def ring():
    req_id = str(uuid.uuid4())
    mqtt_client.publish("door/ring/request", json.dumps({
        "request_id": req_id,
        "doorName": request.json["doorName"]
    }))
    return jsonify(wait_response(req_id))

# @app.route("/face-upload", methods=["POST"])
# def face_upload():
#     img = request.files["face"].read()
#     return jsonify({"mongo_id": base64.b64encode(img).decode()})

@app.route("/face-upload", methods=["POST"])
def face_upload():
    img = request.files["face"].read()
    req_id = str(uuid.uuid4())

    mqtt_client.publish("face/upload/request", json.dumps({
        "request_id": req_id,
        "image": base64.b64encode(img).decode()
    }))

    return jsonify(wait_response(req_id))



# @app.route("/verifyFace", methods=["POST"])
# def verify_face():
#     req_id = str(uuid.uuid4())
#     mqtt_client.publish("face/verify/request", json.dumps({
#         "request_id": req_id,
#         "doorName": request.json["doorName"],
#         "image": request.json["mongoID"]
#     }))
#     return jsonify(wait_response(req_id))


@app.route("/verifyFace", methods=["POST"])
def verify_face():
    data = request.get_json()

    req_id = str(uuid.uuid4())
    mqtt_client.publish("face/verify/request", json.dumps({
        "request_id": req_id,
        "doorName": data["doorName"],
        "face_id": data["face_id"]         # ✅ new key
    }))

    return jsonify(wait_response(req_id))


@app.route("/verifyPin", methods=["POST"])
def verify_pin():
    req_id = str(uuid.uuid4())
    mqtt_client.publish("pin/verify/request", json.dumps({
        "request_id": req_id,
        **request.json
    }))
    return jsonify(wait_response(req_id))

if __name__ == "__main__":
    app.run(port=3000)
