import warnings

warnings.filterwarnings(
    "ignore",
    message=r".*urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
)

import os
import sys
from dotenv import load_dotenv
from viewing_mode import ViewingModeClassifier

def main():
    """Command-line interface for viewing settings classification."""
    if len(sys.argv) != 2:
        print("Usage: cli.py <youtube-title-or-url>", file=sys.stderr)
        sys.exit(1)

    load_dotenv()

    clf = ViewingModeClassifier(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4.1-mini",
    )

    input_text = sys.argv[1]
    settings = clf.classify(input_text)

    # Print both settings
    print(f"Picture Mode: {settings['picture_mode']}")
    print(f"Audio Profile: {settings['audio_profile']}")

if __name__ == "__main__":
    main()
