"""
URL Feature Extractor for CTI-NLP
Extracts 30+ numerical features from a URL instead of using raw text/TF-IDF.
This approach is used by real security tools like VirusTotal and PhishTank.
"""

import re
import math
from urllib.parse import urlparse


# Common legitimate brands that phishers impersonate
SUSPICIOUS_BRANDS = [
    'paypal', 'google', 'facebook', 'microsoft', 'apple', 'amazon',
    'netflix', 'instagram', 'twitter', 'linkedin', 'bank', 'secure',
    'login', 'signin', 'account', 'verify', 'update', 'confirm'
]

# TLDs commonly used in phishing
SUSPICIOUS_TLDS = [
    '.zip', '.xyz', '.top', '.club', '.online', '.site', '.click',
    '.loan', '.win', '.racing', '.work', '.gq', '.ml', '.cf', '.tk'
]

LEGIT_TLDS = ['.com', '.org', '.edu', '.gov', '.net', '.co.in', '.ac.in']


def calculate_entropy(text: str) -> float:
    """
    Shannon entropy - high entropy = more random = more suspicious.
    Legitimate domains like 'google.com' have LOW entropy.
    Phishing domains like 'g00gl3-secure.xyz' have HIGH entropy.
    """
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    entropy = 0.0
    length = len(text)
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def has_ip_address(url: str) -> int:
    """Returns 1 if URL uses an IP instead of a domain name."""
    ip_pattern = r'((\d{1,3}\.){3}\d{1,3})'
    return 1 if re.search(ip_pattern, url) else 0


def extract_features(url: str) -> dict:
    """
    Extract 30+ features from a URL.
    Returns a dictionary of feature_name -> numeric value.
    """
    url = url.strip()

    # Add scheme if missing so urlparse works
    if not url.startswith(('http://', 'https://', 'ftp://')):
        url = 'http://' + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        path = parsed.path.lower()
        query = parsed.query.lower()
        full_url = url.lower()
    except Exception:
        # If parsing fails, return all-suspicious features
        return {f: 1 for f in _feature_names()}

    features = {}

    # ── Length-based features ──
    features['url_length'] = len(url)
    features['domain_length'] = len(domain)
    features['path_length'] = len(path)
    features['query_length'] = len(query)

    # ── Count-based features ──
    features['num_dots'] = url.count('.')
    features['num_hyphens'] = url.count('-')
    features['num_underscores'] = url.count('_')
    features['num_slashes'] = url.count('/')
    features['num_question_marks'] = url.count('?')
    features['num_equals'] = url.count('=')
    features['num_at_signs'] = url.count('@')
    features['num_percent'] = url.count('%')
    features['num_digits_in_domain'] = sum(c.isdigit() for c in domain)
    features['num_subdomains'] = domain.count('.') if domain else 0

    # ── Boolean security features (0 or 1) ──
    features['has_https'] = 1 if parsed.scheme == 'https' else 0
    features['has_ip_address'] = has_ip_address(full_url)
    features['has_at_symbol'] = 1 if '@' in full_url else 0
    features['has_double_slash_redirect'] = 1 if '//' in path else 0
    features['has_prefix_suffix_hyphen'] = 1 if '-' in domain else 0
    features['has_encoded_chars'] = 1 if '%' in full_url else 0
    features['has_port'] = 1 if parsed.port and parsed.port not in (80, 443) else 0

    # ── Suspicious keyword features ──
    features['has_suspicious_brand'] = 1 if any(
        brand in full_url for brand in SUSPICIOUS_BRANDS
    ) else 0
    features['suspicious_keywords_count'] = sum(
        1 for brand in SUSPICIOUS_BRANDS if brand in full_url
    )

    # ── TLD features ──
    tld = '.' + domain.split('.')[-1] if '.' in domain else ''
    features['has_suspicious_tld'] = 1 if tld in SUSPICIOUS_TLDS else 0
    features['has_legit_tld'] = 1 if tld in LEGIT_TLDS else 0

    # ── Entropy features (randomness detection) ──
    features['domain_entropy'] = calculate_entropy(domain.split('.')[0] if domain else '')
    features['path_entropy'] = calculate_entropy(path)
    features['full_url_entropy'] = calculate_entropy(full_url)

    # ── Ratio features ──
    features['digit_ratio'] = (
        sum(c.isdigit() for c in domain) / len(domain) if domain else 0
    )
    features['letter_ratio'] = (
        sum(c.isalpha() for c in domain) / len(domain) if domain else 0
    )

    # ── Structural anomalies ──
    features['abnormal_url'] = 1 if domain not in full_url else 0
    features['url_shortened'] = 1 if any(
        s in domain for s in ['bit.ly', 'tinyurl', 'goo.gl', 't.co', 'ow.ly']
    ) else 0

    return features


def _feature_names():
    """Returns list of all feature names in correct order."""
    return [
        'url_length', 'domain_length', 'path_length', 'query_length',
        'num_dots', 'num_hyphens', 'num_underscores', 'num_slashes',
        'num_question_marks', 'num_equals', 'num_at_signs', 'num_percent',
        'num_digits_in_domain', 'num_subdomains',
        'has_https', 'has_ip_address', 'has_at_symbol',
        'has_double_slash_redirect', 'has_prefix_suffix_hyphen',
        'has_encoded_chars', 'has_port',
        'has_suspicious_brand', 'suspicious_keywords_count',
        'has_suspicious_tld', 'has_legit_tld',
        'domain_entropy', 'path_entropy', 'full_url_entropy',
        'digit_ratio', 'letter_ratio',
        'abnormal_url', 'url_shortened'
    ]


def url_to_feature_vector(url: str) -> list:
    """Returns features as an ordered list (for scikit-learn)."""
    features = extract_features(url)
    return [features.get(name, 0) for name in _feature_names()]


def get_feature_names() -> list:
    return _feature_names()
