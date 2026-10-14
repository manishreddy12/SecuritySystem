import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "apartment_security")
FACE_RECOG_URL = os.getenv("FACE_RECOG_URL", "http://localhost:5000/verify-face")
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(10 * 1024 * 1024)))
REQUEST_TIMEOUT = float(os.getenv("FACE_RECOG_TIMEOUT", "90"))
