from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.debate import router as debate_router

app = FastAPI(title="AI Debate Multi-Agent Platform")

# 프론트엔드(Next.js)에서 SSE 스트림을 직접 fetch하므로 CORS 허용이 필요하다.
# 로컬 개발(localhost:3000)과 Vercel에 배포된 프론트(프로덕션/프리뷰 도메인) 둘 다 허용.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
    # Chrome의 Local/Private Network Access: 공개 도메인(Vercel)에서
    # localhost 백엔드를 부르려면 이 헤더가 있어야 preflight를 통과한다.
    allow_private_network=True,
)

app.include_router(debate_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
