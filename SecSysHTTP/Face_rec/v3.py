from flask import Flask, request, jsonify
from deepface import DeepFace
from PIL import Image
import numpy as np

app = Flask(__name__)

@app.route('/verify-face', methods=['POST'])
def verify_face():
    # IMPORTANT: Do NOT use request.json or request.get_json()

    # 1️⃣ Validate file inputs
    if 'img1' not in request.files or 'img2' not in request.files:
        return jsonify({
            "verified": False,
            "error": "Both image files (img1, img2) are required"
        }), 400

    try:
        # 2️⃣ Load images safely
        img1 = Image.open(request.files['img1']).convert("RGB")
        img2 = Image.open(request.files['img2']).convert("RGB")

        # Debug info (optional but useful)
        print("Image 1:", img1.size, img1.mode)
        print("Image 2:", img2.size, img2.mode)

        # 3️⃣ Convert to NumPy arrays
        img1_np = np.array(img1)
        img2_np = np.array(img2)

        # 4️⃣ DeepFace verification
        result = DeepFace.verify(
            img1_np,
            img2_np,
            model_name="Facenet",
            detector_backend="retinaface",
            distance_metric="cosine",
            enforce_detection=False
        )

        # 5️⃣ Return ONLY what backend needs
        print(result.get("verified"))
        return jsonify({
            "verified": bool(result.get("verified", False))
        }), 200

    except Exception as e:
        print("Face verification error:", str(e))
        return jsonify({
            "verified": False,
            "error": "Face verification failed"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
