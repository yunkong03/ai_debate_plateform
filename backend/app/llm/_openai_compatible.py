from typing import Optional

import httpx


def call_openai_compatible_chat(
    base_url: str,
    model: str,
    prompt: str,
    api_key: Optional[str] = None,
    timeout: float = 60.0,
) -> str:
    """OpenAI 호환 /chat/completions 엔드포인트를 호출하고 답변 텍스트만 반환한다.

    Qwen(로컬)/NVIDIA API 둘 다 이 프로토콜을 쓰므로 공통 호출부만 여기 둔다.
    """
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
