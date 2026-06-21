import json
from openai import OpenAI


SYSTEM_PROMPT = """You are a content summarizer. Given web page content, return a JSON object with exactly these fields:
- "title": A cool, catchy title for the content
- "summary": A short summary in 2-3 sentences
- "topics": An array of exactly 3 main topics discussed
- "deep_dive": An array of exactly 3 suggestions for further reading or exploration related to this content

Return ONLY valid JSON, no markdown code fences, no extra text."""


class OpenAISummarizer:
    def __init__(self, base_url: str = "http://127.0.0.1:8083", model: str = "opencode/mimo-v2.5-free"):
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
        self.model = model

    def summarize(self, content: str, url: str) -> dict:
        prompt = f"URL: {url}\n\nContent:\n{content[:3000]}"
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(text)
        except (json.JSONDecodeError, Exception) as e:
            return {
                "title": f"Note from {url}",
                "summary": f"Content from {url} (summary generation failed: {e})",
                "topics": ["telegram", "link", "note"],
                "deep_dive": [],
            }

    @staticmethod
    def list_models(base_url: str = "http://127.0.0.1:8083") -> list[dict]:
        try:
            client = OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")
            models = client.models.list()
            return [{"id": m.id, "owned_by": getattr(m, "owned_by", "unknown")} for m in models.data]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch models from gateway: {e}")
