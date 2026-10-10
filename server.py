
import time
from uuid import uuid4

from flask import Flask, jsonify, request
from track2.config import get_gemini_api_key
from track2.models import Frame, FrameBatch
from track2.pipeline import Track2Pipeline
from track2.vlm import GeminiVLM, MockVLM

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

api_key = get_gemini_api_key()

if api_key and api_key.strip():
    pipeline = Track2Pipeline(vlm=GeminiVLM(api_key=api_key))
    backend_mode = "gemini"
    print("Track 2 backend: Gemini configured")
else:
    pipeline = Track2Pipeline(vlm=MockVLM())
    backend_mode = "mock"
    print("Track 2 backend: MOCK MODE — no real image analysis")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "service": "A-Eye Track 2 API",
        "mode": backend_mode,
        "real_image_analysis": backend_mode == "gemini",
    })


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return "", 204

    uploaded_image = request.files.get("image")
    if uploaded_image is None:
        return jsonify({
            "error": "No image received. Send it using the 'image' field."
        }), 400

    image_bytes = uploaded_image.read()
    if not image_bytes:
        return jsonify({"error": "The uploaded image is empty."}), 400

    try:
        frame = Frame(
            frame_id=str(uuid4()),
            timestamp=int(time.time() * 1000),
            data=image_bytes,
        )
        result = pipeline.process(FrameBatch(frame))

        return jsonify({
            "mode": backend_mode,
            "is_mock": backend_mode == "mock",
            "result": result.model_dump(mode="json"),
            "assistance_message": result.decision.message,
            "summary": result.summary,
        })
    except Exception as exc:
        app.logger.exception("Image analysis failed")
        return jsonify({
            "error": "Image analysis failed.",
            "details": str(exc),
            "mode": backend_mode,
        }), 500


@app.errorhandler(413)
def image_too_large(_error):
    return jsonify({
        "error": "Image too large. Maximum size is 10 MB."
    }), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
