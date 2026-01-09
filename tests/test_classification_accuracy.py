"""
Comprehensive test suite for viewing mode classification accuracy.
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

# Test cases with expected results
TEST_CASES = [
    # CINEMA tests
    ("Thor Will Return | Avengers: Doomsday in Theaters December 18, 2026", "Cinema"),
    ("Dune: Part Three - Official Trailer (2026)", "Cinema"),
    ("Breaking Bad S05E16 - Felina", "Cinema"),
    ("Star Wars: The Last Jedi - IMAX Trailer", "Cinema"),
    ("Netflix Original Series - Stranger Things S4", "Cinema"),
    ("Marvel Studios' Deadpool & Wolverine | Official Trailer", "Cinema"),
    ("The Batman (2022) - Final Trailer", "Cinema"),
    ("Coming Soon to Theaters - Summer 2026", "Cinema"),
    
    # SPORT tests
    ("Lakers vs Warriors - NBA Highlights", "Sport"),
    ("Premier League Goals - Matchday 15", "Sport"),
    ("Champions League UCL Final 2024 Full Match", "Sport"),
    ("F1 Monaco Grand Prix Highlights", "Sport"),
    ("UFC 300 - Knockout of the Night", "Sport"),
    ("Messi Goal vs Real Madrid", "Sport"),
    ("Super Bowl LVIII Highlights", "Sport"),
    ("Wimbledon 2024 Final - Full Match", "Sport"),
    
    # GAMING tests
    ("Minecraft Survival Let's Play Episode 1", "Gaming"),
    ("GTA 6 First Gameplay Reveal", "Gaming"),
    ("Elden Ring Boss Guide - Malenia Tutorial", "Gaming"),
    ("Fortnite Victory Royale - 20 Kill Game", "Gaming"),
    ("CS2 Pro Tournament Finals", "Gaming"),
    ("The Legend of Zelda: Tears of the Kingdom Walkthrough", "Gaming"),
    ("Call of Duty MW3 Multiplayer Gameplay", "Gaming"),
    ("Speedrun World Record - Super Mario 64", "Gaming"),
    
    # MUSIC tests
    ("Taylor Swift - Anti-Hero (Official Music Video)", "Music"),
    ("The Weeknd - Blinding Lights (Official Audio)", "Music"),
    ("Ed Sheeran - Shape of You (Lyrics)", "Music"),
    ("Coachella 2024 - Full Set", "Music"),
    ("Beethoven Symphony No. 9 - Live Performance", "Music"),
    ("Drake - God's Plan (Official Video)", "Music"),
    ("Coldplay - Yellow (Acoustic Version)", "Music"),
    ("Billie Eilish - Bad Guy (Official Music Video)", "Music"),
    
    # VIVID tests
    ("8K HDR Dolby Vision Nature Documentary", "Vivid"),
    ("4K HDR Demo - Colorful Fireworks", "Vivid"),
    ("Ultra HD 8K Nature Scenes - Wildlife", "Vivid"),
    ("Neon City Lights - 4K Cyberpunk Vibes", "Vivid"),
    ("Colorful Paint Mixing - Satisfying ASMR", "Vivid"),
    ("HDR10+ Demo Video - Test Your TV", "Vivid"),
    ("Northern Lights Aurora Borealis 4K", "Vivid"),
    ("Vibrant Coral Reef - 8K Underwater", "Vivid"),
    
    # STANDARD tests
    ("How to Build a PC - Complete Beginner's Guide", "Standard"),
    ("iPhone 15 Pro Review - Worth the Upgrade?", "Standard"),
    ("Daily News Update - January 7, 2026", "Standard"),
    ("Cooking Pasta Carbonara - Easy Recipe", "Standard"),
    ("Python Tutorial for Beginners", "Standard"),
    ("Product Unboxing - New Tech Gadgets", "Standard"),
    ("Joe Rogan Podcast #2000 - Guest Interview", "Standard"),
    ("TED Talk: The Future of AI", "Standard"),
]

# Edge cases and tricky examples
EDGE_CASES = [
    # Movie game vs game
    ("Spider-Man PS5 Gameplay Walkthrough", "Gaming"),  # Game, not movie
    
    # Concert movie vs concert
    ("Taylor Swift: The Eras Tour Movie - In Theaters Now", "Cinema"),  # Concert movie = cinema
    
    # Sports game (video game) vs sports
    ("FIFA 24 Career Mode Gameplay", "Gaming"),  # Video game
    ("FIFA World Cup 2026 Highlights", "Sport"),  # Real sport
    
    # Music in a movie trailer
    ("Guardians of the Galaxy Vol 3 - Soundtrack Trailer", "Cinema"),  # Movie trailer
    
    # Gaming documentary vs gaming
    ("The History of Nintendo Documentary", "Standard"),  # Documentary about gaming
    
    # HDR gaming
    ("Cyberpunk 2077 4K HDR Ray Tracing Gameplay", "Gaming"),  # Gaming first
]


def run_tests():
    """Run all test cases and report accuracy."""
    load_dotenv()
    
    clf = ViewingModeClassifier(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-5-mini",
    )
    
    print("=" * 80)
    print("VIEWING MODE CLASSIFICATION ACCURACY TEST")
    print("=" * 80)
    print()
    
    # Test main cases
    print("Testing Standard Cases...")
    print("-" * 80)
    
    correct = 0
    total = 0
    failures = []
    
    for text, expected in TEST_CASES:
        result = clf.classify(text)
        total += 1
        
        status = "✓" if result == expected else "✗"
        if result == expected:
            correct += 1
        else:
            failures.append((text, expected, result))
        
        print(f"{status} [{result:8s}] {text[:60]}")
    
    print()
    print("Testing Edge Cases...")
    print("-" * 80)
    
    for text, expected in EDGE_CASES:
        result = clf.classify(text)
        total += 1
        
        status = "✓" if result == expected else "✗"
        if result == expected:
            correct += 1
        else:
            failures.append((text, expected, result))
        
        print(f"{status} [{result:8s}] {text[:60]}")
    
    # Print summary
    print()
    print("=" * 80)
    print(f"RESULTS: {correct}/{total} correct ({100*correct/total:.1f}% accuracy)")
    print("=" * 80)
    
    if failures:
        print()
        print("FAILURES:")
        print("-" * 80)
        for text, expected, got in failures:
            print(f"Expected: {expected:8s} | Got: {got:8s} | Text: {text}")
    
    print()
    
    # Accuracy thresholds
    accuracy = 100 * correct / total
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
