import time
import json
import requests
import re
import logging
from datetime import datetime, timezone

POETRY_API_URL = "https://poetrydb.org/random"

# Basic logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_random_poem():
    try:
        response = requests.get(POETRY_API_URL, timeout=5)
        response.raise_for_status()
        poems = response.json()
        if poems and 'lines' in poems[0]:
            title = poems[0]['title']
            author = poems[0]['author']
            lines = poems[0]['lines']
            return title, author, lines
    except Exception as e:
        logger.warning(f"Failed to fetch poem: {e}")

    return "Unknown", "Unknown", ["Poem unavailable"]

def kebab_case(text):
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text)
    return text.strip('-').lower()

if __name__ == "__main__":
    logger.info("=== Starting poem logger ===")

    while True:
        title, author, lines = fetch_random_poem()
        service_name = kebab_case(title)
        logger.info(f"Poem: {title} by {author} (service: {service_name})")

        for i, line in enumerate(lines, 1):
            log = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "line": line,
                "title": title,
                "author": author,
                "level": "INFO"
            }
            logger.info(json.dumps(log))
            if i < len(lines):
                time.sleep(5)
