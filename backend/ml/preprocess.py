import re
from urllib.parse import urlparse

def clean_url(url: str) -> str:
    """Preprocesses a URL for feature extraction."""
    url = url.lower().strip()
    # Remove http/https to focus on domain/path structure
    url = re.sub(r'^https?://', '', url)
    # Remove www
    url = re.sub(r'^www\.', '', url)
    return url

def extract_features(url: str) -> dict:
    """Extract manual features alongside TF-IDF (optional advanced usage)."""
    parsed = urlparse(url if "://" in url else f"http://{url}")
    return {
        "length": len(url),
        "num_digits": sum(c.isdigit() for c in url),
        "num_special_chars": len(re.findall(r'[^a-zA-Z0-9]', url)),
        "has_ip": 1 if re.search(r'\d+\.\d+\.\d+\.\d+', url) else 0
    }