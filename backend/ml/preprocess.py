"""
CTI-NLP - URL Preprocessor
Kept for backwards compatibility with any code that imports clean_url.
"""

import re
from urllib.parse import urlparse


def clean_url(url: str) -> str:
    """
    Normalize a URL for analysis.
    - Strips whitespace
    - Converts to lowercase
    - Adds http:// if no scheme present
    """
    url = str(url).strip().lower()
    if not url.startswith(('http://', 'https://', 'ftp://')):
        url = 'http://' + url
    return url


def extract_domain(url: str) -> str:
    """Extract just the domain from a URL."""
    url = clean_url(url)
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except Exception:
        return url


def is_valid_url(url: str) -> bool:
    """Check if a string looks like a URL."""
    url = str(url).strip()
    pattern = re.compile(
        r'^(https?://|ftp://)?'
        r'(([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,})'
        r'(:\d+)?(/.*)?$'
    )
    return bool(pattern.match(url))
