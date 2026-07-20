from app.core.config import get_settings
from app.llm.base import BaseLLM
from app.llm.nvidia_api import NvidiaAPILLM
from app.llm.qwen_local import QwenLocalLLM


def get_llm() -> BaseLLM:
    """LLM_PROVIDER 설정에 따라 provider를 고른다(qwen_local | nvidia_api)."""
    if get_settings().llm_provider == "nvidia_api":
        return NvidiaAPILLM()
    return QwenLocalLLM()
