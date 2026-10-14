import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Default to the active local MongoDB port 23017, with fallback/override capability
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:23017")
DB_NAME = os.getenv("DB_NAME", "apartment_security")

FACE_RECOG_URL = os.getenv("FACE_RECOG_URL", "http://localhost:5000/verify-face")
REQUEST_TIMEOUT = float(os.getenv("FACE_RECOG_TIMEOUT", "90"))
