# YouTube Viewing Mode Classifier

A Python-based classifier that determines the optimal **TV picture viewing mode**  
(`Cinema`, `Sport`, `Vivid`, `Music`, `Gaming` or `Standard`) based on a **YouTube video title or URL**.

The system:
- Accepts either a YouTube **title** or **link**
- Fetches real video metadata via **YouTube oEmbed** when a URL is provided
- Uses **OpenAI (GPT-4.x)** to classify the content
- Guarantees a **single-word output**
- Falls back to deterministic heuristics if the API or network fails
- Includes **unit tests** (pytest) with mocked network and API calls

---

## Features

- Title or URL input support
- Real YouTube metadata lookup (oEmbed)
- OpenAI-powered classification
- Strict output validation (always one of four modes)
- Fast responses with caching
- Full pytest test suite
- Offline heuristic fallback

---

## Viewing Modes

The classifier always returns **exactly one** of:

- `Cinema`
- `Sport`
- `Vivid`
- `Music`
- `Gaming`
- `Standard`

If classification is uncertain, it defaults to `Standard`.

---

## Project Structure

py-openai-app/
├── app.py # Example runner
├── viewing_mode.py # Core classification logic
├── dummy_inputs.json # Sample inputs for testing
├── tests/
│ └── test_viewing_mode.py
├── requirements.txt
├── .env # API key (not committed)
└── .gitignore

---

## Requirements

- Python **3.9+**
- OpenAI API key
- Internet access (for OpenAI + YouTube oEmbed)

---

## Installation

### 1) Clone the repository
```bash
git clone <TBD>
cd py-openai-app
```

### 2) Install Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 3) Create a .env file
```bash
OPENAI_API_KEY=your-api-key-here
```