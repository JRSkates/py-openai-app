import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
)

import json
import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from viewing_mode import (
    _heuristic_fallback,
    _validate_settings,
    build_classification_text,
    ViewingModeClassifier,
    ALLOWED_PICTURE_MODES,
    ALLOWED_AUDIO_PROFILES,
)

ALLOWED_MODES = {"Cinema", "Sport", "Vivid", "Music", "Gaming", "Standard"}


def test_validate_settings_only_allows_known_modes():
    """Test that _validate_settings correctly parses JSON strings and validates modes"""
    assert _validate_settings('{"picture_mode": "Movie", "audio_profile": "Movie"}') == {
        "picture_mode": "Movie",
        "audio_profile": "Movie",
    }
    assert _validate_settings('{"picture_mode": "Sports", "audio_profile": "Sports"}') == {
        "picture_mode": "Sports",
        "audio_profile": "Sports",
    }
    assert _validate_settings('{"picture_mode": "Entertainment", "audio_profile": "Entertainment"}') == {
        "picture_mode": "Entertainment",
        "audio_profile": "Entertainment",
    }
    assert _validate_settings('{"picture_mode": "Entertainment", "audio_profile": "Music"}') == {
        "picture_mode": "Entertainment",
        "audio_profile": "Music",
    }
    assert _validate_settings('{"picture_mode": "Graphics", "audio_profile": "Entertainment"}') == {
        "picture_mode": "Graphics",
        "audio_profile": "Entertainment",
    }
    assert _validate_settings('{"picture_mode": "Dynamic", "audio_profile": "Auto"}') == {
        "picture_mode": "Dynamic",
        "audio_profile": "Auto",
    }

    # invalid JSON => defaults to Expert/Auto
    assert _validate_settings('not valid json') == {
        "picture_mode": "Expert",
        "audio_profile": "Auto",
    }

    # invalid modes => defaults
    result = _validate_settings('{"picture_mode": "Unknown", "audio_profile": "Unknown"}')
    assert result["picture_mode"] in ALLOWED_PICTURE_MODES
    assert result["audio_profile"] in ALLOWED_AUDIO_PROFILES
    


def test_heuristic_fallback_basic():
    assert _heuristic_fallback("Official Trailer - New Movie") == {
        "picture_mode": "Movie",
        "audio_profile": "Movie",
    }
    assert _heuristic_fallback("Premier League match highlights") == {
        "picture_mode": "Sports",
        "audio_profile": "Sport",
    }
    assert _heuristic_fallback("8K HDR Dolby Vision demo") == {
        "picture_mode": "Dynamic2",
        "audio_profile": "Auto",
    }
    assert _heuristic_fallback("Live concert performance") == {
        "picture_mode": "Entertainment",
        "audio_profile": "Music",
    }
    assert _heuristic_fallback("Epic gameplay walkthrough") == {
        "picture_mode": "Graphics",
        "audio_profile": "Entertainment",
    }
    assert _heuristic_fallback("Some random text") == {
        "picture_mode": "Expert",
        "audio_profile": "Entertainment",
    }


def test_dummy_json_can_be_loaded():
    path = os.path.join(os.path.dirname(__file__), "..", "dummy_inputs.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert "input" in data[0]


def test_build_classification_text_uses_oembed(monkeypatch):
    def fake_oembed(url: str, timeout_s: float = 2.0):
        return {"title": "UFC 310 Highlights: Best Knockouts", "author_name": "UFC"}

    monkeypatch.setattr("viewing_mode.fetch_youtube_oembed", fake_oembed)

    out = build_classification_text("https://youtu.be/abcdef")
    assert "TITLE: UFC 310 Highlights" in out
    assert "CHANNEL: UFC" in out


def test_classifier_uses_oembed_text_for_urls(monkeypatch):
    """
    Proves classify() uses TITLE/CHANNEL (oEmbed output) rather than the raw URL.
    """
    monkeypatch.setattr(
        "viewing_mode.fetch_youtube_oembed",
        lambda url, timeout_s=2.0: {"title": "GTA V | Let's Play", "author_name": "LetsPlay"},
    )

    captured = {}

    class FakeMessage:
        content = '{"picture_mode": "Graphics", "audio_profile": "Entertainment"}'

    class FakeChoice:
        message = FakeMessage()

    class FakeResp:
        choices = [FakeChoice()]

    def fake_create(*args, **kwargs):
        captured["messages"] = kwargs.get("messages", [])
        return FakeResp()

    # Create classifier and patch AFTER initialization
    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4o-mini")
    monkeypatch.setattr(clf.client.chat.completions, "create", fake_create)

    mode = clf.classify("https://youtu.be/abcdef")
    assert mode == {'audio_profile': 'Entertainment', 'picture_mode': 'Graphics'}

    # Verify that oEmbed data was used in the messages
    assert len(captured["messages"]) == 2
    user_msg = captured["messages"][1]["content"]
    assert "TITLE:" in user_msg
    assert "GTA V" in user_msg
    assert "CHANNEL:" in user_msg
    assert "LetsPlay" in user_msg
    assert "youtu.be" not in user_msg  # should not be the raw URL


def test_classifier_offline_with_mocked_openai(monkeypatch):
    """
    Offline unit test: mock OpenAI so tests are stable and don't use the network.
    """
    class FakeMessage:
        content = '{"picture_mode": "Sports", "audio_profile": "Sports"}'

    class FakeChoice:
        message = FakeMessage()

    class FakeResp:
        choices = [FakeChoice()]

    def fake_create(*args, **kwargs):
        return FakeResp()

    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4o-mini")
    monkeypatch.setattr(clf.client.chat.completions, "create", fake_create)

    result = clf.classify("Some title")
    assert result == {'picture_mode': 'Sports', 'audio_profile': 'Sports'}


def test_classifier_falls_back_when_openai_errors(monkeypatch):
    """
    If OpenAI call fails, classifier should return heuristic result.
    """
    def boom(*args, **kwargs):
        raise RuntimeError("API down")

    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4o-mini")
    monkeypatch.setattr(clf.client.chat.completions, "create", boom)

    # heuristic should identify gaming keywords
    result = clf.classify("GTA V let's play episode 1")
    assert result == {'picture_mode': 'Graphics', 'audio_profile': 'Entertainment'}


def test_classifier_empty_input_returns_standard():
    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4.1-mini")
    assert clf.classify("") == {'audio_profile': 'Auto', 'picture_mode': 'Expert'}
    assert clf.classify("   ") == {'audio_profile': 'Auto', 'picture_mode': 'Expert'}


def test_classifier_caches_results(monkeypatch):
    """
    Same input twice should call OpenAI once due to @lru_cache.
    """
    calls = {"n": 0}

    class FakeMessage:
        content = '{"picture_mode": "Sports", "audio_profile": "Sports"}'

    class FakeChoice:
        message = FakeMessage()

    class FakeResp:
        choices = [FakeChoice()]

    def fake_create(*args, **kwargs):
        calls["n"] += 1
        return FakeResp()

    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4o-mini")
    monkeypatch.setattr(clf.client.chat.completions, "create", fake_create)

    result1 = clf.classify("Chelsea Highlights")
    result2 = clf.classify("Chelsea Highlights")
    assert result1 == {'picture_mode': 'Sports', 'audio_profile': 'Sports'}
    assert result2 == {'picture_mode': 'Sports', 'audio_profile': 'Sports'}
    assert calls["n"] == 1


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OPENAI_API_KEY set")
def test_classifier_live_api_smoke():
    """
    Optional integration test (runs only if OPENAI_API_KEY is set).
    Verify the classifier returns valid picture_mode and audio_profile.
    """
    clf = ViewingModeClassifier(model="gpt-4o-mini")
    result = clf.classify("Official Trailer: Epic Space Movie (4K)")
    
    assert isinstance(result, dict)
    assert "picture_mode" in result
    assert "audio_profile" in result
    assert result["picture_mode"] in ALLOWED_PICTURE_MODES
    assert result["audio_profile"] in ALLOWED_AUDIO_PROFILES
