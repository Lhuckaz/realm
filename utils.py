import requests
import os
from urllib.parse import quote
from dotenv import load_dotenv
import logging

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
TRACKERS_LIST_URL = os.getenv("TRACKERS_LIST_URL")

# ==========================
# Tracker Loader
# ==========================

def load_trackers():
    """
    Load the list of trackers from a URL.
    Returns a list of tracker URLs.
    """
    try:
        response = requests.get(TRACKERS_LIST_URL, timeout=10)
        response.raise_for_status()

        trackers = [
            line.strip() for line in response.text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

        if not trackers:
            logger.warning("No trackers loaded from TRACKERS_LIST_URL")
        return trackers

    except requests.RequestException as e:
        logger.error(f"Error loading trackers: {e}")
        return []

# ==========================
# Magnet Link Builder
# ==========================

def build_magnet_link(info_hash, encoded_display_name, trackers):
    """
    Build a magnet link using info hash, display name, and trackers list.
    """
    magnet = f"magnet:?xt=urn:btih:{info_hash}"
    if encoded_display_name:
        magnet += f"&dn={encoded_display_name}"
    for tracker in trackers:
        magnet += f"&tr={quote(tracker, safe='')}"
    return magnet

# ==========================
# Display Name Extractor
# ==========================

def extract_display_name(title):
    """
    Extracts a clean display name from the stream title.
    """
    if not title:
        return ''
    return title.split('👤')[0].strip()

# ==========================
# Positive Integer Validator
# ==========================

def validate_positive_int(value, default=1):
    """
    Validates that a string value is a positive integer.
    Returns (int, error message or None).
    """
    try:
        num = int(value)
        if num > 0:
            return num, None
        return default, "Must be a positive integer."
    except ValueError:
        return default, "Must be a valid number."
