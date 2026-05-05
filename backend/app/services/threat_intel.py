import requests
from ..config import settings

class ThreatIntelService:
    @staticmethod
    def get_ip_reputation(ip_address: str) -> dict:
        """Query VirusTotal API for IP reputation."""
        if not settings.VIRUSTOTAL_API_KEY:
            return {"warning": "VIRUSTOTAL_API_KEY is missing in .env file.", "ip": ip_address}
        
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"
        headers = {
            "accept": "application/json",
            "x-apikey": settings.VIRUSTOTAL_API_KEY
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json().get('data', {}).get('attributes', {})
                return {
                    "ip": ip_address,
                    "malicious_votes": data.get('last_analysis_stats', {}).get('malicious', 0),
                    "reputation": data.get('reputation', 0),
                    "country": data.get('country', 'Unknown')
                }
            return {"error": f"API returned status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}