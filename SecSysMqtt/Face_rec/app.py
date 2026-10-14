from flask import Flask, request, jsonify
from deepface import DeepFace
from PIL import Image
import numpy as np

app = Flask(__name__)


@app.get('/health')
def health():
    return jsonify({"status": "ok"})


@app.post('/verify-face')
def verify_face():
    if 'img1' not in request.files or 'img2' not in request.files:
        return jsonify({
            "verified": False,
            "error": "Both image files (img1, img2) are required"
        }), 400

    try:
        img1 = np.array(Image.open(request.files['img1']).convert('RGB'))
        img2 = np.array(Image.open(request.files['img2']).convert('RGB'))

        result = DeepFace.verify(
            img1, img2,
            model_name="Facenet",
            detector_backend="retinaface",
            distance_metric="cosine",
            enforce_detection=False
        )

        print("Verification result:", result.get("verified"))
        return jsonify({"verified": bool(result.get("verified", False))}), 200

    except Exception as e:
        print("Face verification error:", str(e))
        return jsonify({
            "verified": False,
            "error": "Face verification failed"
        }), 500


if __name__ == '__main__':
    print("Starting Face Recognition Service on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=False)
