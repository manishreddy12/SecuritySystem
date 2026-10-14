from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import uuid, json, time
from config import MQTT_BROKER, MQTT_PORT
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

responses = {}

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if "request_id" in payload:
            responses[payload["request_id"]] = payload
    except Exception as e:
        print(f"Error parsing MQTT message on {msg.topic}: {e}")

# Support both paho-mqtt v1 and v2
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    mqtt_client = mqtt.Client()

mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe([
    ("door/ring/response", 0),
    ("face/verify/response", 0),
    ("pin/verify/response", 0),
    ("face/upload/response", 0),
])
mqtt_client.loop_start()

def wait_response(req_id, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if req_id in responses:
            return responses.pop(req_id)
        time.sleep(0.05)
    return {"error": "Request timed out waiting for MQTT response"}

@app.route("/ring-doorbell", methods=["POST"])
def ring():
    data = request.get_json(silent=True) or {}
    door_name = data.get("doorName", "")
    if not door_name:
        return jsonify({"error": "doorName is required"}), 400

    req_id = str(uuid.uuid4())
    mqtt_client.publish("door/ring/request", json.dumps({
        "request_id": req_id,
        "doorName": door_name
    }))
    res = wait_response(req_id)
    if "error" in res and res.get("error") == "Request timed out waiting for MQTT response":
        return jsonify(res), 504
    if "error" in res:
        return jsonify(res), 404
    return jsonify(res)

@app.route("/face-upload", methods=["POST"])
def face_upload():
    uploaded = request.files.get("face")
    if not uploaded:
        return jsonify({"error": "Image file field 'face' is required"}), 400
    img = uploaded.read()
    if not img:
        return jsonify({"error": "Uploaded image is empty"}), 400

    req_id = str(uuid.uuid4())
    mqtt_client.publish("face/upload/request", json.dumps({
        "request_id": req_id,
        "image": base64.b64encode(img).decode()
    }))

    res = wait_response(req_id)
    if "error" in res and res.get("error") == "Request timed out waiting for MQTT response":
        return jsonify(res), 504
    return jsonify(res), (201 if res.get("success") else 400)

@app.route("/verifyFace", methods=["POST"])
def verify_face():
    data = request.get_json(silent=True) or {}
    door_name = data.get("doorName", "")
    face_id = data.get("face_id", "")
    if not door_name or not face_id:
        return jsonify({"matched": False, "error": "doorName and face_id are required"}), 400

    req_id = str(uuid.uuid4())
    mqtt_client.publish("face/verify/request", json.dumps({
        "request_id": req_id,
        "doorName": door_name,
        "face_id": face_id
    }))

    res = wait_response(req_id, timeout=120)
    if "error" in res and res.get("error") == "Request timed out waiting for MQTT response":
        return jsonify(res), 504
    if "error" in res and not res.get("matched"):
        return jsonify(res), 404
    return jsonify(res)

@app.route("/verifyPin", methods=["POST"])
def verify_pin():
    data = request.get_json(silent=True) or {}
    req_id = str(uuid.uuid4())
    mqtt_client.publish("pin/verify/request", json.dumps({
        "request_id": req_id,
        **data
    }))
    res = wait_response(req_id)
    if "error" in res and res.get("error") == "Request timed out waiting for MQTT response":
        return jsonify(res), 504
    return jsonify(res)

if __name__ == "__main__":
    print("Starting MQTT HTTP Gateway on http://localhost:3000 ...")
    app.run(port=3000)
