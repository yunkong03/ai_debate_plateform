from app.core.config import get_settings
from app.llm._openai_compatible import call_openai_compatible_chat
from app.llm.base import BaseLLM


class QwenLocalLLM(BaseLLM):
    """Qwen OpenAI 호환 엔드포인트 어댑터. QWEN_BASE_URL + (QWEN_API_KEY 또는 NVIDIA_API_KEY) 사용."""

    def __init__(self, base_url: str = "", model: str = "", api_key: str = ""):
        settings = get_settings()
        self.base_url = base_url or settings.qwen_base_url
        self.model = model or settings.qwen_model
        self.api_key = api_key or settings.qwen_api_key

    def generate(self, prompt: str) -> str:
        if not self.base_url:
            raise RuntimeError("QWEN_BASE_URL이 설정되지 않았습니다 (.env 확인).")
        return call_openai_compatible_chat(self.base_url, self.model, prompt, api_key=self.api_key)
