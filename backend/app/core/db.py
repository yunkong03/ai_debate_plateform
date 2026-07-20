import json
import logging
from typing import Any, Dict, List, Optional

import asyncpg

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS debates (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    workers JSONB NOT NULL,
    transcript JSONB NOT NULL,
    verdict TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def _get_pool() -> Optional[asyncpg.Pool]:
    """DATABASE_URL이 없으면 None을 반환해 기록 기능을 조용히 끈다."""
    global _pool
    database_url = get_settings().database_url
    if not database_url:
        return None
    if _pool is None:
        _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=3)
        async with _pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE)
    return _pool


async def save_debate(
    topic: str, workers: List[str], transcript: List[Dict[str, Any]], verdict: Optional[str]
) -> None:
    """토론 결과 한 건을 기록한다. DB가 없거나 저장에 실패해도 예외를 올리지 않는다
    (기록이 안 된다고 진행 중인 토론이 죽으면 안 된다)."""
    try:
        pool = await _get_pool()
        if pool is None:
            return
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO debates (topic, workers, transcript, verdict) VALUES ($1, $2::jsonb, $3::jsonb, $4)",
                topic,
                json.dumps(workers, ensure_ascii=False),
                json.dumps(transcript, ensure_ascii=False),
                verdict,
            )
    except Exception:
        logger.warning("토론 기록 저장 실패 (무시하고 계속 진행)", exc_info=True)


async def list_debates(limit: int = 20) -> List[Dict[str, Any]]:
    """최근 토론 기록을 반환한다. DB가 없거나 조회 실패 시 빈 리스트."""
    try:
        pool = await _get_pool()
        if pool is None:
            return []
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, topic, verdict, created_at FROM debates ORDER BY id DESC LIMIT $1",
                limit,
            )
        return [
            {
                "id": r["id"],
                "topic": r["topic"],
                "verdict": r["verdict"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ]
    except Exception:
        logger.warning("토론 기록 조회 실패", exc_info=True)
        return []
