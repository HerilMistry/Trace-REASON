from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import anthropic
import openai
from src.config import ANTHROPIC_API_KEY, OPENAI_API_KEY

class LLMProvider(ABC):
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def structured_query(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        pass

class ClaudeProvider(LLMProvider):
    def __init__(self, model: str = "claude-3-sonnet-20240229"):
        self.model = model
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def query(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text

    def structured_query(self, prompt: str, schema: Dict[str, Any], temperature: float = 0.7, max_tokens: int = 2048) -> Dict[str, Any]:
        import json
        
        schema_str = json.dumps(schema, indent=2)
        structured_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_str}"
        
        response = self.query(structured_prompt, temperature=temperature, max_tokens=max_tokens)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {}

class GPTProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        self.model = model
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
        import json
        
        schema_str = json.dumps(schema, indent=2)
        structured_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_str}"
        
        response = self.query(structured_prompt, temperature=temperature, max_tokens=max_tokens)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            return {}

class LLMFactory:
    @staticmethod
    def create_provider(provider_name: str, model: Optional[str] = None) -> LLMProvider:
        if provider_name.lower() == "claude":
            return ClaudeProvider(model or "claude-3-sonnet-20240229")
        elif provider_name.lower() in ["gpt", "openai"]:
            return GPTProvider(model or "gpt-4-turbo-preview")
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
