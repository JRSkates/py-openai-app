import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
)

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from viewing_mode import ViewingModeClassifier

load_dotenv()

app = Flask(__name__)

# Initialize classifier once at startup
classifier = ViewingModeClassifier(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4.1-mini",
)


@app.route("/classify", methods=["POST"])
def classify():
    """
    Classify viewing settings from YouTube URL or title.
    
    Accepts:
    - POST with JSON body: {"input": "YouTube URL or title"}
    
    Returns:
    - JSON: {"picture_mode": "Movie", "audio_profile": "Movie", "input": "..."}
    """
    try:
        data = request.get_json()
        if not data or "input" not in data:
            return jsonify({
                "error": "Missing 'input' field in JSON body",
                "example": {"input": "Thor Will Return | Avengers"}
            }), 400
        input_text = data["input"]
        settings = classifier.classify(input_text)
        
        return jsonify({
            "picture_mode": settings["picture_mode"],
            "audio_profile": settings["audio_profile"],
            "input": input_text
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Classification failed",
            "message": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route("/", methods=["GET"])
def index():
    """API documentation endpoint."""
    return jsonify({
        "name": "Viewing Settings Classifier API",
        "version": "2.0",
        "description": "Classifies content into picture_mode and audio_profile settings",
        "picture_modes": ["Movie", "Sports", "Graphics", "Entertainment", "Dynamic", "Dynamic2", "Expert"],
        "audio_profiles": ["Movie", "Sport", "Music", "Entertainment", "Auto"],
        "endpoints": {
            "/classify": {
                "methods": ["POST"],
                "description": "Classify YouTube content into picture and audio settings",
                "post_example": {
                    "input": "Thor Will Return | Avengers: Doomsday in Theaters"
                },
                "response_example": {
                    "picture_mode": "Movie",
                    "audio_profile": "Movie",
                    "input": "Thor Will Return | Avengers: Doomsday in Theaters"
                }
            },
            "/health": {
                "methods": ["GET"],
                "description": "Health check endpoint"
            }
        }
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
