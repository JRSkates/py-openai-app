"""
Comprehensive test suite for viewing mode classification accuracy.
Tests the dual-setting output: picture_mode + audio_profile

Run this to validate the classifier's reliability across different scenarios.

Usage:
    python3 -m pytest tests/test_classification_accuracy.py -v
    or from project root:
    PYTHONPATH=. python3 tests/test_classification_accuracy.py
"""

import os
import sys

# Ensure parent directory is in path when running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from viewing_mode import ViewingModeClassifier

# Test cases with expected results (picture_mode, audio_profile)
TEST_CASES = [
    # MOVIE tests (Cinema content)
    ("Thor Will Return | Avengers: Doomsday in Theaters December 18, 2026", "Movie", "Movie"),
    ("Dune: Part Three - Official Trailer (2026)", "Movie", "Movie"),
    ("Breaking Bad S05E16 - Felina", "Movie", "Movie"),
    ("Star Wars: The Last Jedi - IMAX Trailer", "Movie", "Movie"),
    ("Netflix Original Series - Stranger Things S4", "Movie", "Movie"),
    ("Marvel Studios' Deadpool & Wolverine | Official Trailer", "Movie", "Movie"),
    ("The Batman (2022) - Final Trailer", "Movie", "Movie"),
    ("Coming Soon to Theaters - Summer 2026", "Movie", "Movie"),
    
    # SPORTS tests
    ("Lakers vs Warriors - NBA Highlights", "Sports", "Sports"),
    ("Premier League Goals - Matchday 15", "Sports", "Sports"),
    ("Champions League UCL Final 2024 Full Match", "Sports", "Sports"),
    ("F1 Monaco Grand Prix Highlights", "Sports", "Sports"),
    ("UFC 300 - Knockout of the Night", "Sports", "Sports"),
    ("Messi Goal vs Real Madrid", "Sports", "Sports"),
    ("Super Bowl LVIII Highlights", "Sports", "Sports"),
    ("Wimbledon 2024 Final - Full Match", "Sports", "Sports"),
    
    # GRAPHICS tests (Gaming content)
    ("Minecraft Survival Let's Play Episode 1", "Graphics", "Entertainment"),
    ("GTA 6 First Gameplay Reveal", "Graphics", "Entertainment"),
    ("Elden Ring Boss Guide - Malenia Tutorial", "Graphics", "Entertainment"),
    ("Fortnite Victory Royale - 20 Kill Game", "Graphics", "Entertainment"),
    ("CS2 Pro Tournament Finals", "Graphics", "Entertainment"),
    ("The Legend of Zelda: Tears of the Kingdom Walkthrough", "Graphics", "Entertainment"),
    ("Call of Duty MW3 Multiplayer Gameplay", "Graphics", "Entertainment"),
    ("Speedrun World Record - Super Mario 64", "Graphics", "Entertainment"),
    
    # ENTERTAINMENT tests (Music content)
    ("Taylor Swift - Anti-Hero (Official Music Video)", "Entertainment", "Music"),
    ("The Weeknd - Blinding Lights (Official Audio)", "Entertainment", "Music"),
    ("Ed Sheeran - Shape of You (Lyrics)", "Entertainment", "Music"),
    ("Coachella 2024 - Full Set", "Entertainment", "Music"),
    ("Beethoven Symphony No. 9 - Live Performance", "Entertainment", "Music"),
    ("Drake - God's Plan (Official Video)", "Entertainment", "Music"),
    ("Coldplay - Yellow (Acoustic Version)", "Entertainment", "Music"),
    ("Billie Eilish - Bad Guy (Official Music Video)", "Entertainment", "Music"),
    
    # DYNAMIC tests (HDR/4K/8K demos)
    ("8K HDR Dolby Vision Nature Documentary", "Dynamic", "Auto"),
    ("4K HDR Demo - Colorful Fireworks", "Dynamic", "Auto"),
    ("Ultra HD 8K Nature Scenes - Wildlife", "Dynamic", "Auto"),
    ("Neon City Lights - 4K Cyberpunk Vibes", "Dynamic", "Auto"),
    ("Colorful Paint Mixing - Satisfying ASMR", "Dynamic", "Auto"),
    ("HDR10+ Demo Video - Test Your TV", "Dynamic2", "Auto"),
    ("Northern Lights Aurora Borealis 4K", "Dynamic", "Auto"),
    ("Vibrant Coral Reef - 8K Underwater", "Dynamic", "Auto"),
    
    # EXPERT tests (Reviews, tutorials, standard content)
    ("How to Build a PC - Complete Beginner's Guide", "Expert", "Entertainment"),
    ("iPhone 15 Pro Review - Worth the Upgrade?", "Expert", "Entertainment"),
    ("Daily News Update - January 7, 2026", "Expert", "Entertainment"),
    ("Cooking Pasta Carbonara - Easy Recipe", "Expert", "Entertainment"),
    ("Python Tutorial for Beginners", "Expert", "Entertainment"),
    ("Product Unboxing - New Tech Gadgets", "Expert", "Entertainment"),
    ("Joe Rogan Podcast #2000 - Guest Interview", "Expert", "Entertainment"),
    ("TED Talk: The Future of AI", "Expert", "Entertainment"),
]

# Edge cases and tricky examples
EDGE_CASES = [
    # Movie game vs game
    ("Spider-Man PS5 Gameplay Walkthrough", "Graphics", "Entertainment"),  # Game, not movie
    
    # Concert movie vs concert
    ("Taylor Swift: The Eras Tour Movie - In Theaters Now", "Movie", "Movie"),  # Concert movie = cinema
    
    # Sports game (video game) vs sports
    ("FIFA 24 Career Mode Gameplay", "Graphics", "Entertainment"),  # Video game
    ("FIFA World Cup 2026 Highlights", "Sports", "Sports"),  # Real sport
    
    # Music in a movie trailer
    ("Guardians of the Galaxy Vol 3 - Soundtrack Trailer", "Movie", "Movie"),  # Movie trailer
    
    # Gaming documentary vs gaming
    ("The History of Nintendo Documentary", "Expert", "Entertainment"),  # Documentary about gaming
    
    # HDR gaming
    ("Cyberpunk 2077 4K HDR Ray Tracing Gameplay", "Graphics", "Entertainment"),  # Gaming first
]


def run_tests():
    """Run all test cases and report accuracy."""
    load_dotenv()
    
    clf = ViewingModeClassifier(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )
    
    print("=" * 80)
    print("VIEWING MODE CLASSIFICATION ACCURACY TEST")
    print("Dual-Setting Output: picture_mode + audio_profile")
    print("=" * 80)
    print()
    
    # Test main cases
    print("Testing Standard Cases...")
    print("-" * 80)
    
    correct_picture = 0
    correct_audio = 0
    correct_both = 0
    total = 0
    failures = []
    
    for text, expected_picture, expected_audio in TEST_CASES:
        result = clf.classify(text)
        total += 1
        
        picture_match = result["picture_mode"] == expected_picture
        audio_match = result["audio_profile"] == expected_audio
        both_match = picture_match and audio_match
        
        if picture_match:
            correct_picture += 1
        if audio_match:
            correct_audio += 1
        if both_match:
            correct_both += 1
        else:
            failures.append((text, expected_picture, expected_audio, result["picture_mode"], result["audio_profile"]))
        
        status = "✓" if both_match else "✗"
        result_str = f"{result['picture_mode']}/{result['audio_profile']}"
        expected_str = f"{expected_picture}/{expected_audio}"
        
        print(f"{status} [{result_str:25s}] {text[:50]}")
    
    print()
    print("Testing Edge Cases...")
    print("-" * 80)
    
    for text, expected_picture, expected_audio in EDGE_CASES:
        result = clf.classify(text)
        total += 1
        
        picture_match = result["picture_mode"] == expected_picture
        audio_match = result["audio_profile"] == expected_audio
        both_match = picture_match and audio_match
        
        if picture_match:
            correct_picture += 1
        if audio_match:
            correct_audio += 1
        if both_match:
            correct_both += 1
        else:
            failures.append((text, expected_picture, expected_audio, result["picture_mode"], result["audio_profile"]))
        
        status = "✓" if both_match else "✗"
        result_str = f"{result['picture_mode']}/{result['audio_profile']}"
        expected_str = f"{expected_picture}/{expected_audio}"
        
        print(f"{status} [{result_str:25s}] {text[:50]}")
    
    # Print summary
    print()
    print("=" * 80)
    print(f"RESULTS:")
    print(f"  Both Correct: {correct_both}/{total} ({100*correct_both/total:.1f}%)")
    print(f"  Picture Mode: {correct_picture}/{total} ({100*correct_picture/total:.1f}%)")
    print(f"  Audio Profile: {correct_audio}/{total} ({100*correct_audio/total:.1f}%)")
    print("=" * 80)
    
    if failures:
        print()
        print("FAILURES:")
        print("-" * 80)
        for text, exp_pic, exp_aud, got_pic, got_aud in failures:
            print(f"Expected: {exp_pic:12s}/{exp_aud:12s} | Got: {got_pic:12s}/{got_aud:12s}")
            print(f"  Text: {text}")
            print()
    
    # Accuracy thresholds
    accuracy = 100 * correct_both / total
    if accuracy >= 95:
        print("EXCELLENT: Accuracy >= 95% - Production ready!")
    elif accuracy >= 90:
        print("GOOD: Accuracy >= 90% - Acceptable for most use cases")
    elif accuracy >= 80:
        print("FAIR: Accuracy >= 80% - Consider improvements")
    else:
        print("POOR: Accuracy < 80% - Needs significant improvement")
    
    return accuracy


if __name__ == "__main__":
    run_tests()
