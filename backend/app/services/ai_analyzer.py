import openai
from ..config import settings

openai.api_key = settings.OPENAI_API_KEY

class CTIAnalyzer:
    @staticmethod
    async def analyze_report(report_text: str) -> dict:
        """Uses LLM to extract IoCs (Indicators of Compromise) from a text report."""
        if not settings.OPENAI_API_KEY:
            return {"error": "OpenAI API key not configured."}
            
        prompt = f"""
        Analyze the following Cyber Threat Intelligence report. 
        Extract malicious IP addresses, Domains, and TTPs (Tactics, Techniques, and Procedures).
        Return ONLY a JSON object with keys: 'ips', 'domains', 'ttps', 'summary'.
        
        Report: {report_text}
        """
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        # Parse and return JSON (ensure error handling in prod)
        return eval(response.choices[0].message.content)