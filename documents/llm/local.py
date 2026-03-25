import requests, os, json

class LocalLLM(LLMBackend):
    def classify(self, text: str) -> dict:
        url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate"
        payload = {
            "model": os.getenv("OLLAMA_MODEL", "llama3"),
            "prompt": PROMPT_TEMPLATE.format(text=text[:4000]),
            "stream": False
        }
        r = requests.post(url, json=payload, timeout=30)
        return json.loads(r.json()["response"])