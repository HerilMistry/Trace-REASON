from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json
import groq
from src.config import GROQ_API_KEY

class LLMProvider(ABC):
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def structured_query(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        pass

class GroqProvider(LLMProvider):
    def __init__(self, model: str = "llama3-70b-8192"):
        self.model = model
        self.client = groq.Groq(api_key=GROQ_API_KEY)

    def query(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def structured_query(self, prompt: str, schema: Dict[str, Any], temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        schema_str = json.dumps(schema, indent=2)
        structured_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema. Do not add any extra markdown formatting around the JSON, just the raw JSON:\n{schema_str}"
        
        response = self.query(structured_prompt, temperature=temperature, max_tokens=max_tokens)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response[start:end])
                except json.JSONDecodeError:
                    return {}
            return {}

class LLMFactory:
    @staticmethod
    def create_provider(provider_name: str, model: Optional[str] = None) -> LLMProvider:
        # Default to Groq no matter what was passed previously
        return GroqProvider(model or "llama3-70b-8192")
