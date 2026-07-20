from app.core.config import get_settings
from app.llm._openai_compatible import call_openai_compatible_chat
from app.llm.base import BaseLLM


class NvidiaAPILLM(BaseLLM):
    """NVIDIA OpenAI 호환 API 어댑터. NVIDIA_API_KEY 사용."""

    def __init__(self, api_key: str = "", model: str = "", base_url: str = ""):
        settings = get_settings()
        self.api_key = api_key or settings.nvidia_api_key
        self.model = model or settings.nvidia_model
        self.base_url = base_url or settings.nvidia_base_url

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("NVIDIA_API_KEY가 설정되지 않았습니다 (.env 확인).")
        return call_openai_compatible_chat(self.base_url, self.model, prompt, api_key=self.api_key)
