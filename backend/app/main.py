from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.debate import router as debate_router

app = FastAPI(title="AI Debate Multi-Agent Platform")

# 프론트엔드(Next.js, 기본 localhost:3000)에서 SSE 스트림을 직접 fetch하므로 CORS 허용이 필요하다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(debate_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
