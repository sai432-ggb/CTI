import re

def is_valid_ip(ip: str) -> bool:
    """Validates if a string is a proper IPv4 address."""
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    if pattern.match(ip):
        # Additional check to ensure each octet is 0-255
        return all(0 <= int(octet) <= 255 for octet in ip.split('.'))
    return False

def format_api_response(status: str, data: dict, message: str = "") -> dict:
    """Standardizes the JSON response format for the frontend."""
    return {
        "status": status,
        "message": message,
        "data": data
    }