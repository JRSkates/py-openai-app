# YouTube TV Settings Classifier

A Python-based classifier that determines optimal **TV viewing settings** (picture mode and audio profile) based on YouTube video titles or URLs. The application analyzes content and returns appropriate TV settings for the best viewing experience.

The system:

- Accepts either a YouTube **title** or **URL**
- Fetches real video metadata via **YouTube oEmbed** when a URL is provided
- Uses **OpenAI (GPT-4.1-mini)** to intelligently classify content
- Returns both **picture mode** and **audio profile** settings
- Falls back to deterministic heuristics if the API or network fails
- Available as both **Flask REST API** and **command-line tool**
- Includes **unit tests** (pytest) with mocked network and API calls

---

## Features

- **Dual-interface**: REST API (Flask) and CLI tool
- Title or URL input support
- Real YouTube metadata lookup (oEmbed)
- OpenAI-powered classification with GPT-4.1-mini
- Dual-output: picture mode + audio profile
- Strict output validation
- Response caching for performance
- Full pytest test suite
- Offline heuristic fallback

---

## TV Settings

The classifier returns TWO settings:

### Picture Modes

- `Movie` - Films, TV shows, cinematic content, trailers
- `Sports` - Live sports, highlights, matches
- `Graphics` - Video games, gameplay, streaming
- `Entertainment` - Music videos, concerts, general entertainment
- `Dynamic` - High-quality demos, HDR/4K content
- `Dynamic2` - Ultra vivid content, extreme brightness/color
- `Expert` - Reviews, tutorials, standard content (default)

### Audio Profiles

- `Movie` - Cinematic audio for films and TV shows
- `Sport` - Sports audio enhancement
- `Music` - Music-optimized audio
- `Entertainment` - General entertainment audio
- `Auto` - Automatic audio detection (default)

---

## Project Structure

```
py-openai-app/
├── app.py                          # Flask REST API server
├── cli.py                          # Command-line interface
├── viewing_mode.py                 # Core classification logic
├── dummy_inputs.json               # Sample inputs for testing
├── tests/
│   ├── test_viewing_mode.py        # Unit tests for classifier
│   └── test_classification_accuracy.py  # Accuracy tests
├── requirements.txt
├── .env                            # API key (not committed)
├── .gitignore
├── README.md
├── FLASK_API_NOTES.md             # API documentation
└── RESTRUCTURE_NOTES.md           # Development notes
```

---

## Requirements

- Python **3.9+**
- OpenAI API key
- Internet access (for OpenAI + YouTube oEmbed)

---

## Installation

### 1) Clone the repository

```bash
git clone <repository-url>
cd py-openai-app
```

### 2) Install Dependencies

```bash
pip install -r requirements.txt
```

### 3) Create a .env file

```bash
OPENAI_API_KEY=your-api-key-here
```

---

## Usage

### Option 1: REST API (Flask)

Start the Flask server:

```bash
python app.py
```

The API runs on `http://localhost:5000` with the following endpoints:

#### POST /classify

Classify content into TV settings:

```bash
curl -X POST http://localhost:5000/classify \
  -H "Content-Type: application/json" \
  -d '{"input": "Thor Will Return | Avengers: Doomsday in Theaters"}'
```

Response:

```json
{
  "picture_mode": "Movie",
  "audio_profile": "Movie",
  "input": "Thor Will Return | Avengers: Doomsday in Theaters"
}
```

#### GET /

View API documentation and available settings

#### GET /health

Health check endpoint

### Option 2: Command-Line Interface

Run directly from the command line:

```bash
python cli.py "Thor Will Return | Avengers: Doomsday in Theaters"
```

Output:

```
Picture Mode: Movie
Audio Profile: Movie
```

You can also provide YouTube URLs:

```bash
python cli.py "https://www.youtube.com/watch?v=example"
```

---

## Testing

Run the full test suite:

```bash
pytest
```

Run specific tests:

```bash
pytest tests/test_viewing_mode.py
pytest tests/test_classification_accuracy.py
```

Tests include:

- Mocked OpenAI API calls
- Mocked YouTube oEmbed responses
- Classification accuracy validation
- Error handling and fallback scenarios

---

## Example Classifications

| Input                                       | Picture Mode  | Audio Profile |
| ------------------------------------------- | ------------- | ------------- |
| "Avengers: Endgame Official Trailer"        | Movie         | Movie         |
| "Lakers vs Warriors Highlights"             | Sports        | Sport         |
| "Taylor Swift - Anti-Hero (Official Video)" | Entertainment | Music         |
| "Elden Ring Boss Guide"                     | Graphics      | Entertainment |
| "8K HDR Nature Demo"                        | Dynamic       | Auto          |
| "iPhone 15 Review"                          | Expert        | Entertainment |
