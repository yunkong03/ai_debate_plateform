from typing import List, Optional

from pydantic import BaseModel


class DebateRequest(BaseModel):
    topic: str


class ExpertOpinion(BaseModel):
    expert: str
    content: str


class DebateResponse(BaseModel):
    topic: str
    experts: List[str] = []
    rounds: int = 0
    opinions: List[ExpertOpinion] = []
    summary: Optional[str] = None
    verdict: Optional[str] = None
