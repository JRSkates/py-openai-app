import os
import re
from functools import lru_cache
from typing import Literal, Optional

import requests
from openai import OpenAI

ViewingMode = Literal["Cinema", "Sport", "Vivid", "Music", "Gaming","Standard"]
ALLOWED: set[str] = {"Cinema", "Sport", "Vivid", "Music", "Gaming", "Standard"}

SYSTEM_PROMPT = """You are an expert at classifying YouTube videos or TV content into the optimal TV picture mode.

Analyze the input text and classify it into EXACTLY ONE of these modes:
Cinema, Sport, Vivid, Music, Gaming, Standard

Classification Rules (in order of priority):

CINEMA - Movies, TV shows, cinematic content:
• Keywords: trailer, movie, film, cinematic, IMAX, scene, clip, episode, series, season, netflix, hbo, disney+
• Locations: theater, theatre, cinema, "in theaters", "now showing"
• TV Shows: Look for patterns like "S##E##" (S05E16), "Season #", show titles with episode numbers
• Indicators: release dates, film titles, director names, actor names, "official trailer", "original series"
• Franchises: Marvel, DC, Star Wars, Disney, Pixar, Universal, Warner Bros
• TV Series: Breaking Bad, Stranger Things, Game of Thrones, The Office, Friends, etc.
• Examples: "Avengers: Doomsday in Theaters", "Dune Part 3 Official Trailer", "Breaking Bad S5E16", "Stranger Things S4"

SPORT - Live sports, highlights, matches:
• Sports: football, soccer, basketball, baseball, tennis, golf, racing, boxing, MMA, cricket, rugby
• Leagues: NBA, NFL, MLB, NHL, Premier League, Champions League, UCL, La Liga, Serie A, F1
• Keywords: highlights, match, game, vs, goal, touchdown, home run, knockout, race, lap, tournament
• Examples: "Lakers vs Warriors Highlights", "Premier League Goals", "F1 Monaco Grand Prix"

GAMING - Video games, gameplay, streaming:
• Keywords: gameplay, gaming, let's play, walkthrough, speedrun, stream, playthrough
• Guides: boss guide, game tutorial, build guide, tips and tricks (for games), game guide
• Platforms: PS5, Xbox, PC gaming, Nintendo Switch, Steam Deck
• Game titles: Fortnite, Minecraft, GTA, Call of Duty, FIFA, Valorant, League of Legends, Elden Ring, Zelda, Pokemon, CS2, Counter-Strike, Cyberpunk
• Esports: tournament, championship, competitive, esports, pro player
• Examples: "Elden Ring Boss Guide", "Fortnite Victory Royale", "CS2 Tournament Finals", "Minecraft Let's Play"

MUSIC - Music videos, concerts, performances:
• Keywords: official music video, lyric video, lyrics, audio, official audio, MV, live performance, official video
• Content: song, album, single, track, concert, tour, festival, acoustic, cover, symphony, orchestra
• Venues: Coachella, Glastonbury, Lollapalooza, Madison Square Garden, concert hall
• Patterns: "Artist - Song Title", "(Official Video)", "(Lyrics)", "(Acoustic)", "- Topic", "Full Set"
• Examples: "Taylor Swift - Cardigan (Official Video)", "Coachella 2024 Full Set", "Beethoven Symphony No. 9", "Drake - God's Plan (Official Video)"

VIVID - High-quality demos, colorful content, nature:
• Technical: HDR, 4K, 8K, Dolby Vision, Ultra HD, HDR10+, demo, test, showcase
• Visual: colorful, colourful, vibrant, neon, rainbow, stunning visuals, eye candy, beautiful
• Nature: aurora, northern lights, wildlife, landscape, timelapse, slow motion, macro, coral reef, nature scenes
• Special: fireworks, ASMR with vibrant colors, satisfying videos
• Patterns: "8K Nature", "4K Wildlife", "Aurora Borealis", technical specs + nature
• Examples: "8K HDR Dolby Vision Nature Demo", "Neon City Lights 4K", "Northern Lights Aurora Borealis 4K", "Colorful Paint Mixing"

STANDARD - Everything else:
• News, talk shows, interviews, podcasts, vlogs, tutorials, reviews, documentaries
• Educational content, how-to videos, cooking, DIY, unboxing
• Anything that doesn't clearly fit the above categories

Priority Rules:
1. If multiple categories could apply, choose the PRIMARY content type
2. Gaming content with HDR/4K → Gaming (gameplay takes priority over technical quality)
3. Gaming footage in a review → Gaming (not Standard)
4. Movie clips/trailers → Cinema (even if in a review/reaction)
5. Concert documentary → Music (not Cinema)
6. Sports documentary → Sport (not Cinema)
7. When uncertain → Standard

Output: Reply with ONLY ONE WORD (Cinema, Sport, Vivid, Music, Gaming, or Standard). No explanation, no punctuation, no extra text."""

def _normalize_input(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def _looks_like_youtube_url(text: str) -> bool:
    t = text.strip().lower()
    return ("youtube.com/" in t) or ("youtu.be/" in t)

def _validate_mode(mode: str) -> ViewingMode:
    cleaned = " ".join(mode.strip().split())

    if cleaned in ALLOWED:
        return cleaned  

    # Try case-insensitive match
    for m in ("Cinema", "Sport", "Vivid", "Music", "Gaming", "Standard"):
        if m.lower() in cleaned.lower():
            return m  

    return "Standard"

def _heuristic_fallback(text: str) -> ViewingMode:
    """
    Enhanced keyword-based fallback with weighted scoring.
    Returns the mode with the highest confidence score.
    """
    t = text.lower()
    
    # Score each category (higher = more confident)
    scores = {
        "Gaming": 0,
        "Music": 0,
        "Sport": 0,
        "Cinema": 0,
        "Vivid": 0,
        "Standard": 0
    }

    # Gaming
    gaming_strong = ["gameplay", "let's play", "lets play", "walkthrough", "speedrun", 
                     "playthrough", "esports", "gaming channel", "boss guide", "game guide"]
    gaming_weak = ["gaming", "gamer", "stream", "twitch", "ps5", "xbox", "nintendo"]
    gaming_titles = ["gta", "minecraft", "fortnite", "call of duty", "cod", "valorant", 
                     "league of legends", "fifa", "elden ring", "zelda", "pokemon", "cs2", 
                     "counter-strike", "spider-man"]
    
    scores["Gaming"] += sum(2 for k in gaming_strong if k in t)
    scores["Gaming"] += sum(1 for k in gaming_weak if k in t)
    scores["Gaming"] += sum(2 for k in gaming_titles if k in t)
    
    # Specific game detection
    if "cyberpunk 2077" in t or "cyberpunk2077" in t:
        scores["Gaming"] += 2
    
    if any(k in t for k in ["gameplay", "playthrough", "let's play", "walkthrough"]):
        scores["Gaming"] += 2

    # Music 
    music_strong = ["official music video", "official video", "official audio", "lyric video",
                    "live concert", "music video", "full album", "full set", "(lyrics)", "(acoustic)"]
    music_weak = ["music", "song", "audio", "mv", "concert", "live performance", "acoustic",
                  "cover", "remix", "dj set", "festival", "tour", "symphony", "orchestra"]
    
    if " - " in t and any(k in t for k in ["official", "lyrics", "audio", "video", "acoustic"]):
        scores["Music"] += 2
    
    scores["Music"] += sum(3 for k in music_strong if k in t)
    scores["Music"] += sum(1 for k in music_weak if k in t)

    # Sport 
    sport_strong = ["highlights", "full match", "extended highlights", "vs ", " vs.", 
                    "match highlights", "goal", "touchdown"]
    sport_leagues = ["premier league", "nba", "nfl", "mlb", "nhl", "ucl", "champions league",
                     "la liga", "serie a", "bundesliga", "f1", "formula 1", "ufc", "fifa world cup"]
    sport_weak = ["match", "game", "race", "boxing", "mma", "tennis", "football", "soccer",
                  "basketball", "baseball"]
    
    scores["Sport"] += sum(3 for k in sport_strong if k in t)
    scores["Sport"] += sum(2 for k in sport_leagues if k in t)
    scores["Sport"] += sum(1 for k in sport_weak if k in t)

    # Cinema
    cinema_strong = ["official trailer", "official teaser", "in theaters", "in theatres",
                     "now playing", "coming soon", "imax", "original series"]
    cinema_medium = ["trailer", "teaser", "movie", "film", "cinema", "theater", "theatre",
                     "official clip", "scene", "episode", "series", "season"]
    cinema_studios = ["marvel", "dc comics", "disney", "pixar", "warner bros", "universal pictures",
                      "netflix", "hbo", "prime video", "apple tv+"]
    cinema_indicators = ["will return", "part 2", "part 3", "s0", "s1", "s2", "s3", "s4", "s5"]
    
    # Check for TV series pattern
    if re.search(r's\d+e\d+', t):
        scores["Cinema"] += 3
    
    scores["Cinema"] += sum(3 for k in cinema_strong if k in t)
    scores["Cinema"] += sum(2 for k in cinema_medium if k in t)
    scores["Cinema"] += sum(2 for k in cinema_studios if k in t)
    scores["Cinema"] += sum(1 for k in cinema_indicators if k in t)

    # Vivid
    vivid_strong = ["4k hdr", "8k", "dolby vision", "hdr10", "ultra hd", "hdr demo"]
    vivid_nature = ["aurora", "northern lights", "aurora borealis", "4k wildlife", "8k nature",
                    "coral reef", "nature scenes", "timelapse"]
    vivid_weak = ["hdr", "4k", "colorful", "colourful", "vibrant", "neon",
                  "satisfying", "asmr", "wildlife", "landscape"]
    
    scores["Vivid"] += sum(3 for k in vivid_strong if k in t)
    scores["Vivid"] += sum(2 for k in vivid_nature if k in t)
    scores["Vivid"] += sum(1 for k in vivid_weak if k in t)

    # Get the highest scoring category
    max_score = max(scores.values())
    
    # Only return non-Standard if confidence is high enough (score >= 2)
    if max_score >= 2:
        for mode, score in scores.items():
            if score == max_score and mode != "Standard":
                return mode  # type: ignore
    
    return "Standard"

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
        return r.json()
    except Exception:
        return None


def build_classification_text(input_text: str) -> str:
    """
    If input is a YouTube URL and oEmbed succeeds, return a short metadata string
    (title + channel). Otherwise return the raw normalized input.
    """
    text = _normalize_input(input_text)
    if not text:
        return ""

    if _looks_like_youtube_url(text):
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
    def classify(self, youtube_title_or_url: str) -> ViewingMode:
        # Use oEmbed metadata when a URL is provided
        text_for_model = build_classification_text(youtube_title_or_url)
        if not text_for_model:
            return "Standard"

        try:
            resp = self.client.responses.create(
                model=self.model,
                temperature=0,
                max_output_tokens=16,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text_for_model},
                ],
            )
            return _validate_mode(resp.output_text)
        except Exception:
            return _heuristic_fallback(text_for_model)


def classify_viewing_mode(youtube_title_or_url: str) -> ViewingMode:
    """Convenience function."""
    return ViewingModeClassifier().classify(youtube_title_or_url)
