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
    """Command-line interface for viewing mode classification."""
    if len(sys.argv) != 2:
        print("Usage: cli.py <youtube-title-or-url>", file=sys.stderr)
        sys.exit(1)

    load_dotenv()

    clf = ViewingModeClassifier(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-5-mini",
    )

    input_text = sys.argv[1]
    mode = clf.classify(input_text)

    # entire program output
    print(mode)

if __name__ == "__main__":
    main()
