import os
import httpx
from rei.models.adapter import ModelAdapter
from rei.core.cancellation import CancelToken
from rei.egress.gate import EgressGate

class NIMPlannerError(Exception):
    pass

class CloudAssistedPlanner(ModelAdapter):
    """NVIDIA NIM API adapter for complex LLM planning (MOD-02).
    
    Uses NVIDIA's OpenAI-compatible endpoint. Requires NIM_API_KEY env var.
    """
    
    def __init__(self, egress_gate: EgressGate, model_name: str = "meta/llama-3.2-11b-vision-instruct") -> None:
        self.egress_gate = egress_gate
        self.model_name = model_name
        self.api_key = os.environ.get("NIM_API_KEY")
        if not self.api_key:
            raise NIMPlannerError("NIM_API_KEY environment variable is not set.")
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    async def generate(self, prompt: str, cancel_token: CancelToken, deadline_ms: int = 15000) -> str:
        cancel_token.raise_if_cancelled()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 256,
            "stream": False
        }
        
        timeout = httpx.Timeout(deadline_ms / 1000.0)
        
        try:
            response = await self.egress_gate.post_http(
                destination="integrate.api.nvidia.com",
                purpose="planner",
                url=self.base_url,
                headers=headers,
                json_body=payload,
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            
            cancel_token.raise_if_cancelled()
            
            content = data["choices"][0]["message"]["content"]
            return self._extract_json(content)
            
        except httpx.HTTPStatusError as e:
            raise NIMPlannerError(f"NIM API returned error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise NIMPlannerError(f"NIM API connection failed: {e}")

    def _extract_json(self, content: str) -> str:
        """Extracts JSON block from markdown if present."""
        if "```json" in content:
            content = content.split("```json")[1]
            if "```" in content:
                content = content.split("```")[0]
        elif "```" in content:
            content = content.split("```")[1]
            if "```" in content:
                content = content.split("```")[0]
        return content.strip()
