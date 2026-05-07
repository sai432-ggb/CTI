import json
from openai import OpenAI
from ..config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class CTIAnalyzer:
    @staticmethod
    async def analyze_report(report_text: str) -> dict:
        """Uses LLM to extract IoCs (Indicators of Compromise) from a text report."""
        if not settings.OPENAI_API_KEY:
            return {"error": "OpenAI API key not configured."}
            
        try:
            prompt = f"""
            Analyze the following Cyber Threat Intelligence report. 
            Extract malicious IP addresses, Domains, and TTPs (Tactics, Techniques, and Procedures).
            Return ONLY a JSON object with keys: 'ips', 'domains', 'ttps', 'summary'.
            
            Report: {report_text}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}]
            )
            
            # Safe JSON parsing instead of eval
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"CTI analysis failed: {str(e)}")
            return {
                "error": f"CTI analysis failed: {str(e)}",
                "ips": [],
                "domains": [],
                "ttps": [],
                "summary": "Analysis failed due to API error"
            }