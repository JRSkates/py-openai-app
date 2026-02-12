import os
import re
from functools import lru_cache
from typing import Literal, Optional, TypedDict

import requests
from openai import OpenAI

PictureMode = Literal["Entertainment", "Dynamic", "Expert", "Movie", "Sports", "Graphics", "Dynamic2"]
AudioProfile = Literal["Music", "Movie", "Sports", "Auto", "Entertainment"]

ALLOWED_PICTURE_MODES: set[str] = {"Entertainment", "Dynamic", "Expert", "Movie", "Sports", "Graphics", "Dynamic2"}
ALLOWED_AUDIO_PROFILES: set[str] = {"Music", "Movie", "Sports", "Auto", "Entertainment"}

class ViewingSettings(TypedDict):
    picture_mode: PictureMode
    audio_profile: AudioProfile

SYSTEM_PROMPT = """You are an expert at classifying YouTube videos or TV content to determine optimal TV settings.

Analyze the input text and return TWO settings in JSON format:
1. picture_mode: The optimal picture/display mode
2. audio_profile: The optimal audio profile

PICTURE MODES (choose ONE):
• Movie - Movies, films, TV shows, cinematic content, trailers
  - Keywords: movie, film, trailer, cinema, IMAX, theater, series, episode, netflix, hbo
  - TV patterns: S##E##, Season #
  - Examples: "Avengers in Theaters", "Breaking Bad S5E16", "Official Trailer"

• Sports - Live sports, highlights, matches
  - Keywords: highlights, match, game, vs, goal, tournament, race
  - Leagues: NBA, NFL, Premier League, UCL, F1, UFC
  - Examples: "Lakers vs Warriors", "Champions League Final"

• Graphics - Video games, gameplay, streaming
  - Keywords: gameplay, gaming, let's play, walkthrough, speedrun, esports
  - Games: Fortnite, Minecraft, GTA, Call of Duty, Elden Ring, CS2
  - Examples: "Boss Guide", "Gameplay Walkthrough"

• Entertainment - Music videos, concerts, general entertainment
  - Keywords: music video, concert, live performance, lyrics, official video
  - Patterns: "Artist - Song", festival, acoustic, cover
  - Examples: "Taylor Swift (Official Video)", "Coachella Full Set"

• Dynamic - High-quality demos, colorful content (vivid/bright)
  - Keywords: HDR, 4K, 8K, Dolby Vision, demo, colorful, vibrant, neon
  - Examples: "8K HDR Demo", "Neon City Lights 4K"

• Dynamic2 - Extra vivid content, extreme brightness/color
  - Keywords: ultra HDR, HDR10+, extreme colors, stunning visuals
  - Nature: aurora, northern lights, coral reef (when 8K/HDR)
  - Examples: "Northern Lights 8K HDR", "Ultra Vivid Demo"

• Expert - Custom/technical content, reviews, tutorials, standard content
  - Keywords: review, tutorial, how-to, unboxing, podcast, interview, news
  - Examples: "iPhone Review", "Python Tutorial", "Tech News"

AUDIO PROFILES (choose ONE):
• Movie - Cinematic audio for films and TV shows
  - Use when picture_mode is Movie
  - Movie trailers, series, cinematic content

• Sports - Sports audio enhancement
  - Use when picture_mode is Sports
  - Live sports, match highlights, tournaments

• Music - Music-optimized audio
  - Use when picture_mode is Entertainment AND content is music-related
  - Music videos, concerts, live performances

• Entertainment - General entertainment audio
  - Use when picture_mode is Entertainment, Graphics, or Expert
  - Gaming, reviews, tutorials, vlogs


DECISION RULES:
1. Movie content → picture_mode: Movie, audio_profile: Movie
2. Sports content → picture_mode: Sports, audio_profile: Sport
3. Music videos/concerts → picture_mode: Entertainment, audio_profile: Music
4. Gaming content → picture_mode: Graphics, audio_profile: Entertainment
5. HDR/4K demos → picture_mode: Dynamic/Dynamic2, audio_profile: Auto
6. Reviews/tutorials → picture_mode: Expert, audio_profile: Entertainment
7. Gaming with HDR → picture_mode: Graphics (gameplay priority)

Output format: Reply with ONLY valid JSON in this exact format:
{"picture_mode": "Movie", "audio_profile": "Movie"}

No explanation, no extra text, just the JSON object."""

def _normalise_input(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def _looks_like_youtube_url(text: str) -> bool:
    t = text.strip().lower()
    return ("youtube.com/" in t) or ("youtu.be/" in t)

def _validate_settings(response: str) -> ViewingSettings:
    """Parse and validate the JSON response from the API."""
    import json
    
    try:
        data = json.loads(response.strip())
        picture_mode = data.get("picture_mode", "")
        audio_profile = data.get("audio_profile", "")
        
        # Validate picture mode
        if picture_mode not in ALLOWED_PICTURE_MODES:
            # Try case-insensitive match
            for mode in ALLOWED_PICTURE_MODES:
                if mode.lower() == picture_mode.lower():
                    picture_mode = mode
                    break
            else:
                picture_mode = "Expert"  # Default fallback
        
        # Validate audio profile
        if audio_profile not in ALLOWED_AUDIO_PROFILES:
            # Try case-insensitive match
            for profile in ALLOWED_AUDIO_PROFILES:
                if profile.lower() == audio_profile.lower():
                    audio_profile = profile
                    break
            else:
                audio_profile = "Auto"  # Default fallback
        
        return ViewingSettings(
            picture_mode=picture_mode,  # type: ignore
            audio_profile=audio_profile  # type: ignore
        )
    except (json.JSONDecodeError, KeyError, AttributeError):
        # If parsing fails, return default
        return ViewingSettings(picture_mode="Expert", audio_profile="Auto")

def _heuristic_fallback(text: str) -> ViewingSettings:
    """
    Enhanced keyword-based fallback with weighted scoring.
    Returns both picture_mode and audio_profile based on content analysis.
    """
    t = text.lower()
    
    # Score each category
    scores = {
        "Movie": 0,      # Picture mode
        "Sports": 0,
        "Graphics": 0,
        "Entertainment": 0,
        "Dynamic": 0,
        "Dynamic2": 0,
        "Expert": 0
    }

    # Gaming (Graphics picture mode)
    gaming_strong = ["gameplay", "let's play", "lets play", "walkthrough", "speedrun", 
                     "playthrough", "esports", "gaming channel", "boss guide", "game guide"]
    gaming_weak = ["gaming", "gamer", "stream", "twitch", "ps5", "xbox", "nintendo"]
    gaming_titles = ["gta", "minecraft", "fortnite", "call of duty", "cod", "valorant", 
                     "league of legends", "fifa", "elden ring", "zelda", "pokemon", "cs2", 
                     "counter-strike", "spider-man"]
    
    scores["Graphics"] += sum(2 for k in gaming_strong if k in t)
    scores["Graphics"] += sum(1 for k in gaming_weak if k in t)
    scores["Graphics"] += sum(2 for k in gaming_titles if k in t)
    
    if "cyberpunk 2077" in t or "cyberpunk2077" in t:
        scores["Graphics"] += 2
    
    if any(k in t for k in ["gameplay", "playthrough", "let's play", "walkthrough"]):
        scores["Graphics"] += 2

    # Music (Entertainment picture mode with Music audio)
    music_strong = ["official music video", "official video", "official audio", "lyric video",
                    "live concert", "music video", "full album", "full set", "(lyrics)", "(acoustic)"]
    music_weak = ["music", "song", "audio", "mv", "concert", "live performance", "acoustic",
                  "cover", "remix", "dj set", "festival", "tour", "symphony", "orchestra"]
    
    if " - " in t and any(k in t for k in ["official", "lyrics", "audio", "video", "acoustic"]):
        scores["Entertainment"] += 2
    
    scores["Entertainment"] += sum(3 for k in music_strong if k in t)
    scores["Entertainment"] += sum(1 for k in music_weak if k in t)

    # Sport (Sports picture mode)
    sport_strong = ["highlights", "full match", "extended highlights", "vs ", " vs.", 
                    "match highlights", "goal", "touchdown"]
    sport_leagues = ["premier league", "nba", "nfl", "mlb", "nhl", "ucl", "champions league",
                     "la liga", "serie a", "bundesliga", "f1", "formula 1", "ufc", "fifa world cup"]
    sport_weak = ["match", "game", "race", "boxing", "mma", "tennis", "football", "soccer",
                  "basketball", "baseball"]
    
    scores["Sports"] += sum(3 for k in sport_strong if k in t)
    scores["Sports"] += sum(2 for k in sport_leagues if k in t)
    scores["Sports"] += sum(1 for k in sport_weak if k in t)

    # Cinema (Movie picture mode)
    cinema_strong = ["official trailer", "official teaser", "in theaters", "in theatres",
                     "now playing", "coming soon", "imax", "original series"]
    cinema_medium = ["trailer", "teaser", "movie", "film", "cinema", "theater", "theatre",
                     "official clip", "scene", "episode", "series", "season"]
    cinema_studios = ["marvel", "dc comics", "disney", "pixar", "warner bros", "universal pictures",
                      "netflix", "hbo", "prime video", "apple tv+"]
    cinema_indicators = ["will return", "part 2", "part 3", "s0", "s1", "s2", "s3", "s4", "s5"]
    
    if re.search(r's\d+e\d+', t):
        scores["Movie"] += 3
    
    scores["Movie"] += sum(3 for k in cinema_strong if k in t)
    scores["Movie"] += sum(2 for k in cinema_medium if k in t)
    scores["Movie"] += sum(2 for k in cinema_studios if k in t)
    scores["Movie"] += sum(1 for k in cinema_indicators if k in t)

    # Vivid (Dynamic/Dynamic2 picture modes)
    vivid_strong = ["4k hdr", "8k", "dolby vision", "hdr10", "ultra hd", "hdr demo", "hdr10+"]
    vivid_nature = ["aurora", "northern lights", "aurora borealis", "4k wildlife", "8k nature",
                    "coral reef", "nature scenes", "timelapse"]
    vivid_weak = ["hdr", "4k", "colorful", "colourful", "vibrant", "neon",
                  "satisfying", "asmr", "wildlife", "landscape"]
    
    # Check for extra vivid indicators
    extra_vivid = ["ultra hdr", "hdr10+", "8k hdr", "extreme colors", "stunning visuals"]
    if any(k in t for k in extra_vivid):
        scores["Dynamic2"] += 4
    else:
        scores["Dynamic"] += sum(3 for k in vivid_strong if k in t)
    
    scores["Dynamic"] += sum(2 for k in vivid_nature if k in t)
    scores["Dynamic"] += sum(1 for k in vivid_weak if k in t)
    scores["Dynamic2"] += sum(1 for k in vivid_weak if k in t)

    # Determine picture mode
    max_score = max(scores.values())
    picture_mode = "Expert"  # Default
    
    if max_score >= 2:
        for mode, score in scores.items():
            if score == max_score:
                picture_mode = mode
                break
    
    # Determine audio profile based on picture mode
    audio_profile = "Auto"
    
    if picture_mode == "Movie":
        audio_profile = "Movie"
    elif picture_mode == "Sports":
        audio_profile = "Sport"
    elif picture_mode == "Entertainment":
        # Check if music-related
        if any(k in t for k in music_strong + music_weak):
            audio_profile = "Music"
        else:
            audio_profile = "Entertainment"
    elif picture_mode == "Graphics":
        audio_profile = "Entertainment"
    elif picture_mode in ["Dynamic", "Dynamic2"]:
        audio_profile = "Auto"
    else:  # Expert
        audio_profile = "Entertainment"
    
    return ViewingSettings(
        picture_mode=picture_mode,  # type: ignore
        audio_profile=audio_profile  # type: ignore
    )

@lru_cache(maxsize=512)
def fetch_youtube_oembed(url: str, timeout_s: float = 2.0) -> Optional[dict]:
    """
    Fetch metadata via YouTube oEmbed.
    Returns dict like: { "title": "...", "author_name": "...", "thumbnail_url": "...", ... }
    or None on failure.
    """
    endpoint = "https://www.youtube.com/oembed"
    try:
        r = requests.get(endpoint, params={"url": url, "format": "json"}, timeout=timeout_s)
        r.raise_for_status()
        print(f"Debug: Fetched oEmbed data: {r.json()}")
        return r.json()
    except Exception:
        print(f"Warning: Failed to fetch oEmbed for URL: {url}")
        return None


def build_classification_text(input_text: str) -> str:
    """
    If input is a YouTube URL and oEmbed succeeds, return a short metadata string
    (title + channel). Otherwise return the raw normalized input.
    """
    text = _normalise_input(input_text)
    print(f"Debug: Normalized input text: {text}")
    if not text:
        return ""

    if _looks_like_youtube_url(text):
        print("Debug: Detected YouTube URL, fetching oEmbed metadata.")
        meta = fetch_youtube_oembed(text)
        if meta and meta.get("title"):
            title = meta.get("title", "")
            channel = meta.get("author_name", "")
            # Keep it short but informative
            return f"TITLE: {title}\nCHANNEL: {channel}".strip()

    return text


class ViewingModeClassifier:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-mini"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    @lru_cache(maxsize=512)
    def classify(self, youtube_title_or_url: str) -> ViewingSettings:
        """
        Classify content with dual-layer validation.
        Returns both picture_mode and audio_profile.
        """
        text_for_model = build_classification_text(youtube_title_or_url)
        if not text_for_model:
            print("Warning: Empty input after normalization, defaulting to Expert/Auto.")
            return ViewingSettings(picture_mode="Expert", audio_profile="Auto")

        # Get heuristic prediction as fallback
        heuristic_settings = _heuristic_fallback(text_for_model)

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=1,
                max_completion_tokens=100,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text_for_model},
                ],
            )
            print(f"Debug: OpenAI response: {resp.choices[0].message.content}")
            
            api_settings = _validate_settings(resp.choices[0].message.content or "")
            
            # Trust API result
            return api_settings
            
        except Exception as e:
            print(f"Warning: OpenAI API call failed: {e}, using heuristic fallback.")
            return heuristic_settings


def classify_viewing_mode(youtube_title_or_url: str) -> ViewingSettings:
    """Convenience function."""
    return ViewingModeClassifier().classify(youtube_title_or_url)
