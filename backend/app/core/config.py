import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# backend/.env를 명시적으로 로드한다(cwd에 상관없이 항상 backend/.env를 찾도록).
# 파일이 없으면 조용히 넘어간다(python-dotenv 기본 동작).
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class Settings:
    """런타임 설정. backend/.env(python-dotenv)로 로드된 프로세스 환경변수를 읽는다."""

    llm_provider: str = os.getenv("LLM_PROVIDER", "qwen_local")
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "")
    # 이 프로젝트의 "로컬" Qwen은 NVIDIA 발급 키로 인증하는 게이트웨이 뒤에 있다
    # (QWEN_BASE_URL의 /v1/models로 직접 확인함). 별도 QWEN_API_KEY가 없으면 재사용.
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")
    qwen_model: str = os.getenv("QWEN_MODEL", "Qwen/Qwen3.5-35B-A3B")
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nvidia_base_url: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    nvidia_model: str = os.getenv("NVIDIA_MODEL", "qwen/qwen2.5-7b-instruct")
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "")
    # Neon(Postgres) 연결 문자열. 비어있으면 기록 기능은 조용히 꺼진다(데모가 DB에 의존하지 않도록).
    database_url: str = os.getenv("DATABASE_URL", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
