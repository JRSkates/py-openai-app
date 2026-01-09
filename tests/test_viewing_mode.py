import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
)

import json
import os
import pytest

from viewing_mode import (
    _heuristic_fallback,
    _validate_mode,
    ViewingModeClassifier,
    build_classification_text,
)

ALLOWED_MODES = {"Cinema", "Sport", "Vivid", "Music", "Gaming", "Standard"}


def test_validate_mode_only_allows_known_modes():
    assert _validate_mode("Cinema") == "Cinema"
    assert _validate_mode("Sport") == "Sport"
    assert _validate_mode("Vivid") == "Vivid"
    assert _validate_mode("Music") == "Music"
    assert _validate_mode("Gaming") == "Gaming"
    assert _validate_mode("Standard") == "Standard"

    # trims whitespace
    assert _validate_mode(" Cinema ") == "Cinema"

    # invalid => Standard
    assert _validate_mode("SomethingElse") == "Standard"

    # recovers embedded valid word
    assert _validate_mode("Mode: Gaming") == "Gaming"
    assert _validate_mode("Gaming.") == "Gaming"


def test_heuristic_fallback_basic():
    assert _heuristic_fallback("Official Trailer - New Movie") == "Cinema"
    assert _heuristic_fallback("Premier League match highlights") == "Sport"
    assert _heuristic_fallback("8K HDR Dolby Vision demo") == "Vivid"
    assert _heuristic_fallback("Live concert performance") == "Music"
    assert _heuristic_fallback("Epic gameplay walkthrough") == "Gaming"
    assert _heuristic_fallback("Some random text") == "Standard"


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
    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4.1-mini")

    monkeypatch.setattr(
        "viewing_mode.fetch_youtube_oembed",
        lambda url, timeout_s=2.0: {"title": "GTA V | Let's Play", "author_name": "LetsPlay"},
    )

    captured = {}

    class FakeResp:
        output_text = "Gaming"

    def fake_create(*args, **kwargs):
        captured["input"] = kwargs["input"]
        return FakeResp()

    monkeypatch.setattr(clf.client.responses, "create", fake_create)

    mode = clf.classify("https://youtu.be/abcdef")
    assert mode == "Gaming"

    # input is a list of messages: [system, user]
    user_msg = captured["input"][1]["content"]
    assert "TITLE:" in user_msg
    assert "CHANNEL:" in user_msg
    assert "youtu.be" not in user_msg  # should not be the raw URL


def test_classifier_offline_with_mocked_openai(monkeypatch):
    """
    Offline unit test: mock OpenAI so tests are stable and don't use the network.
    """
    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4.1-mini")

    class FakeResp:
        output_text = "Sport"

    def fake_create(*args, **kwargs):
        return FakeResp()

    monkeypatch.setattr(clf.client.responses, "create", fake_create)

    assert clf.classify("Some title") == "Sport"


def test_classifier_falls_back_when_openai_errors(monkeypatch):
    """
    If OpenAI call fails, classifier should return heuristic result.
    """
    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4.1-mini")

    def boom(*args, **kwargs):
        raise RuntimeError("API down")

    monkeypatch.setattr(clf.client.responses, "create", boom)

    # heuristic should identify gaming keywords
    assert clf.classify("GTA V let's play episode 1") == "Gaming"


def test_classifier_empty_input_returns_standard():
    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4.1-mini")
    assert clf.classify("") == "Standard"
    assert clf.classify("   ") == "Standard"


def test_classifier_caches_results(monkeypatch):
    """
    Same input twice should call OpenAI once due to @lru_cache.
    """
    clf = ViewingModeClassifier(api_key="test-key", model="gpt-4.1-mini")
    calls = {"n": 0}

    class FakeResp:
        output_text = "Sport"

    def fake_create(*args, **kwargs):
        calls["n"] += 1
        return FakeResp()

    monkeypatch.setattr(clf.client.responses, "create", fake_create)

    assert clf.classify("Chelsea Highlights") == "Sport"
    assert clf.classify("Chelsea Highlights") == "Sport"
    assert calls["n"] == 1


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OPENAI_API_KEY set")
def test_classifier_live_api_smoke():
    """
    Optional integration test (runs only if OPENAI_API_KEY is set).
    Avoid strict expectations — just ensure it's one of the allowed strings.
    """
    clf = ViewingModeClassifier(model="gpt-4.1-mini")
    mode = clf.classify("Official Trailer: Epic Space Movie (4K)")
    assert mode in ALLOWED_MODES
