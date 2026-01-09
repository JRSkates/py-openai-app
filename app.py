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
    model="gpt-5-mini",
)


@app.route("/classify", methods=["POST"])
def classify():
    """
    Classify viewing mode from YouTube URL or title.
    
    Accepts:
    - POST with JSON body: {"input": "YouTube URL or title"}
    
    Returns:
    - JSON: {"viewing_mode": "Cinema", "input": "..."}
    """
    try:
        data = request.get_json()
        if not data or "input" not in data:
            return jsonify({
                "error": "Missing 'input' field in JSON body",
                "example": {"input": "Thor Will Return | Avengers"}
            }), 400
        input_text = data["input"]
        viewing_mode = classifier.classify(input_text)
        
        return jsonify({
            "viewing_mode": viewing_mode,
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
        "name": "Viewing Mode Classifier API",
        "version": "1.0",
        "endpoints": {
            "/classify": {
                "methods": ["POST"],
                "description": "Classify YouTube content into viewing modes",
                "post_example": {
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
