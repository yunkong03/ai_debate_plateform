from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """LLM 어댑터 공통 인터페이스. Qwen(로컬)/NVIDIA API 교체를 위한 추상화."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
