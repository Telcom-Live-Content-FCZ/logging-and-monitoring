import socket
import time
import json
import requests
import re
import logging
from datetime import datetime, timezone

LOGSTASH_HOST = "logstash"  # This only works inside Docker containers
LOGSTASH_PORT = 5000
POETRY_API_URL = "https://poetrydb.org/random"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_random_poem():
    logger.info("Starting to fetch random poem from Poetry API")
    try:
        logger.debug(f"Making request to: {POETRY_API_URL}")
        response = requests.get(POETRY_API_URL, timeout=5)
        logger.debug(f"Response status code: {response.status_code}")
        response.raise_for_status()
        poems = response.json()
        logger.debug(f"Received {len(poems)} poem(s) from API")
        if poems and 'lines' in poems[0]:
            title = poems[0]['title']
            author = poems[0]['author']
            lines_count = len(poems[0]['lines'])
            logger.info(f"Successfully fetched poem: '{title}' by {author} ({lines_count} lines)")
            return title, author, poems[0]['lines']
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching poem: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching poem: {e}")
    
    logger.warning("Using fallback poem data")
    return "Unknown", "Unknown", ["Poem unavailable"]

def kebab_case(text):
    # Replace non-alphanumeric with hyphens, lowercase, strip multiple hyphens
    logger.debug(f"Converting text to kebab-case: '{text}'")
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text)
    result = text.strip('-').lower()
    logger.debug(f"Kebab-case result: '{result}'")
    return result

def send_line_to_logstash(line, title, author, service_name):
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": line,
        "title": title,
        "author": author,
        "level": "INFO",
        "service": service_name
    }

    logger.debug(f"Preparing to send log entry to {LOGSTASH_HOST}:{LOGSTASH_PORT}")
    logger.debug(f"Log data: {json.dumps(log, indent=2)}")
    
    try:
        logger.debug(f"Creating socket connection to {LOGSTASH_HOST}:{LOGSTASH_PORT}")
        with socket.create_connection((LOGSTASH_HOST, LOGSTASH_PORT)) as sock:
            message = json.dumps(log) + "\n"
            sock.sendall(message.encode("utf-8"))
            logger.info(f"Successfully sent log: [{title}] {line[:50]}{'...' if len(line) > 50 else ''}")
            logger.debug(f"Sent {len(message)} bytes to Logstash")
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed for {LOGSTASH_HOST}: {e}")
    except socket.timeout as e:
        logger.error(f"Connection timeout to {LOGSTASH_HOST}:{LOGSTASH_PORT}: {e}")
    except ConnectionRefusedError as e:
        logger.error(f"Connection refused to {LOGSTASH_HOST}:{LOGSTASH_PORT}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending log to Logstash: {e}")
        logger.debug(f"Failed log data: {json.dumps(log)}")

if __name__ == "__main__":
    logger.info("=== Starting log sender application ===")
    logger.info(f"Logstash target: {LOGSTASH_HOST}:{LOGSTASH_PORT}")
    logger.info(f"Poetry API URL: {POETRY_API_URL}")
    
    title, author, lines = fetch_random_poem()
    service_name = kebab_case(title)
    
    logger.info(f"Generated service name: '{service_name}'")
    logger.info(f"Starting to send {len(lines)} lines with 5-second intervals")
    
    for i, line in enumerate(lines, 1):
        logger.debug(f"Processing line {i}/{len(lines)}")
        send_line_to_logstash(line, title, author, service_name)
        if i < len(lines):  # Don't sleep after the last line
            logger.debug(f"Sleeping for 5 seconds before next line...")
            time.sleep(5)

    logger.info("=== All lines sent successfully. Exiting. ===")
