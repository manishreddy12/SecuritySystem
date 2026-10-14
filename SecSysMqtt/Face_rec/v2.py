print("run v3.py not v2.py")
# from flask import Flask, request, jsonify
# from deepface import DeepFace
# from PIL import Image
# import numpy as np
# import io

# app = Flask(__name__)



# @app.route('/verify-face', methods=['POST'])
# def verify_face():
#     # Check both files exist
#     if 'img1' not in request.files or 'img2' not in request.files:
#         return jsonify({"error": "Both image files (img1, img2) are required"}), 400

#     img1_file = request.files['img1']
#     img2_file = request.files['img2']

#     # Read images into PIL Image for debugging prints
#     img1 = Image.open(img1_file)
#     img2 = Image.open(img2_file)

#     # Print images info for debugging (size, mode)
#     print("Verifying Image 1:", img1.size, img1.mode)
#     print("Verifying Image 2:", img2.size, img2.mode)

#     # Convert images to numpy arrays for DeepFace
#     img1_np = np.array(img1)
#     img2_np = np.array(img2)

#     try:
#         # result = DeepFace.verify(img1_np, img2_np, model_name='Facenet', distance_metric='cosine')
#         result = DeepFace.verify(img1_np,img2_np,model_name='Facenet',detector_backend='retinaface',distance_metric='cosine',enforce_detection=False)
#         print(result)
#         # return jsonify(result), 200
#         return jsonify({"verified": bool(result.get("verified", False))}), 200
#     except Exception as e:
#         return jsonify({"error": "DeepFace verification failed", "details": str(e)}), 500


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)




# @app.route('/verify-face', methods=['POST'])
# def verify_face():
#     if 'img1' not in request.files or 'img2' not in request.files:
#         return jsonify({"error": "Both image files (img1, img2) are required"}), 400

#     img1_file = request.files['img1']
#     img2_file = request.files['img2']
#     img1_file.seek(0)
#     img2_file.seek(0)

#     img1 = Image.open(img1_file)
#     img2 = Image.open(img2_file)

#     if img1.mode != 'RGB':
#         img1 = img1.convert('RGB')
#     if img2.mode != 'RGB':
#         img2 = img2.convert('RGB')

#     print("Verifying Image 1:", img1.size, img1.mode)
#     print("Verifying Image 2:", img2.size, img2.mode)

#     img1_np = np.array(img1)
#     img2_np = np.array(img2)

#     try:
#         result = DeepFace.verify(img1_np, img2_np, model_name='Facenet', distance_metric='cosine')
#         print(result)
#         return jsonify(result), 200
#     except Exception as e:
#         import traceback
#         print("DeepFace verification exception:")
#         traceback.print_exc()
#         return jsonify({"error": "DeepFace verification failed", "details": str(e)}), 500
