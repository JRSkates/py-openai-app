# Flask API Implementation Notes

## Overview

Converted the command-line viewing mode classifier into a REST API using Flask, enabling HTTP-based classification requests with JSON responses.

## Changes Made

### 1. app.py - Flask Web Server

**Previous:** Command-line script that accepted arguments via `sys.argv`

```python
# Old approach
python3 app.py "YouTube Title Here"
# Output: Cinema
```

**Current:** Flask REST API with HTTP endpoints

```python
# New approach
curl -X POST http://127.0.0.1:5000/classify \
  -H "Content-Type: application/json" \
  -d '{"input": "YouTube Title Here"}'
# Output: {"viewing_mode": "Cinema", "input": "YouTube Title Here"}
```

### 2. Key Components

#### Classifier Initialization

```python
classifier = ViewingModeClassifier(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5-mini",
)
```

- Initialised **once** at application startup (efficient)
- Reuses same instance for all requests
- Maintains LRU cache for repeated queries

#### HTTP Endpoints

**POST/GET `/classify`** - Main classification endpoint

- Accepts: JSON body with `{"input": "text"}` or query param `?input=text`
- Returns: `{"viewing_mode": "Cinema|Sport|Vivid|Music|Gaming|Standard", "input": "..."}`
- Error handling: Returns 400 for missing input, 500 for classification failures

**GET `/health`** - Health check

- Returns: `{"status": "healthy"}`
- Used for monitoring and load balancer checks

**GET `/`** - API documentation

- Returns: JSON describing all endpoints and usage examples
- Self-documenting API

### 3. Request Flow

```
HTTP Request → Flask Route → Extract Input → ViewingModeClassifier.classify()
                                                    ↓
                          Enhanced System Prompt + OpenAI API
                                                    ↓
                          Weighted Heuristic Fallback (if API fails)
                                                    ↓
JSON Response ← Format Response ← Validate Mode ← Classification Result
```

### 4. Classification Logic (Unchanged)

All improvements from `viewing_mode.py` are preserved:

- ✅ Enhanced system prompt with detailed rules
- ✅ TV series detection (S##E##)
- ✅ Weighted keyword scoring (strong/medium/weak)
- ✅ Dual-layer validation (API + fallback)
- ✅ 100% accuracy on test suite

### 5. Supporting Files

**cli.py** - Preserved command-line interface

```bash
python3 cli.py "YouTube Title"
```

Maintains original functionality for quick testing.

**requirements.txt** - Added Flask dependency

```
openai
python-dotenv
requests
pytest
flask
```

## Usage Examples

### cURL (Command Line)

```bash
# POST request
curl -X POST http://127.0.0.1:5000/classify \
  -H "Content-Type: application/json" \
  -d '{"input": "Thor Will Return | Avengers: Doomsday in Theaters"}'

# GET request
curl "http://127.0.0.1:5000/classify?input=Lakers+vs+Warriors"

# Health check
curl http://127.0.0.1:5000/health
```

### Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:5000/classify",
    json={"input": "Taylor Swift - Anti-Hero (Official Music Video)"}
)

result = response.json()
print(result["viewing_mode"])  # "Music"
```

### JavaScript

```javascript
fetch("http://127.0.0.1:5000/classify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ input: "FIFA World Cup Highlights" }),
})
  .then((res) => res.json())
  .then((data) => console.log(data.viewing_mode)); // "Sport"
```

### C++ (libcurl)

```cpp
CURL* curl = curl_easy_init();
curl_easy_setopt(curl, CURLOPT_URL, "http://127.0.0.1:5000/classify");
curl_easy_setopt(curl, CURLOPT_POSTFIELDS, "{\"input\":\"Gaming content\"}");
struct curl_slist* headers = curl_slist_append(NULL, "Content-Type: application/json");
curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
curl_easy_perform(curl);
```

## Running the Server

### Development

```bash
python3 app.py
# Runs on http://127.0.0.1:5000
# Debug mode enabled (auto-reload on code changes)
```

### Production

For production deployment, use a WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

- `-w 4`: 4 worker processes
- `-b 0.0.0.0:5000`: Bind to all interfaces on port 5000

## API Response Format

### Success Response

```json
{
  "viewing_mode": "Cinema",
  "input": "Thor Will Return | Avengers: Doomsday in Theaters"
}
```

### Error Response (400 - Missing Input)

```json
{
  "error": "Missing 'input' field in JSON body",
  "example": { "input": "Thor Will Return | Avengers" }
}
```

### Error Response (500 - Classification Failed)

```json
{
  "error": "Classification failed",
  "message": "API key invalid"
}
```

## Architecture Benefits

1. **Stateless** - Each request is independent
2. **Cacheable** - LRU cache speeds up repeated queries
3. **Scalable** - Can run multiple workers/containers
4. **Language Agnostic** - Any HTTP client can use it
5. **Testable** - Easy to write integration tests
6. **Monitorable** - Health endpoint for load balancers

## Testing

### Manual Testing

```bash
# Start server
python3 app.py

# In another terminal
curl -X POST http://127.0.0.1:5000/classify \
  -H "Content-Type: application/json" \
  -d '{"input": "Test Input"}'
```

### Automated Testing

The existing test suite still works:

```bash
python3 tests/test_classification_accuracy.py
```

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your-api-key-here
FLASK_ENV=development  # or production
FLASK_DEBUG=1          # Enable debug mode
```

### Server Settings

In `app.py`:

```python
app.run(
    host="0.0.0.0",  # Listen on all interfaces
    port=5000,        # Port number
    debug=True        # Debug mode (disable in production)
)
```

## Future Enhancements (Optional)

- **CORS Support**: Add `flask-cors` for browser clients
- **Rate Limiting**: Add `flask-limiter` to prevent abuse
- **Authentication**: API keys or JWT tokens
- **Logging**: Request/response logging for debugging
- **Metrics**: Track classification accuracy and response times
- **Batch Endpoint**: Classify multiple inputs at once
- **Async Processing**: Queue long-running requests

## Notes

- Flask's built-in server is for **development only**
- Use gunicorn/uwsgi for production
- Debug mode auto-reloads on code changes
- Classifier instance is shared across requests (memory efficient)
- All classification logic from `viewing_mode.py` is preserved unchanged
