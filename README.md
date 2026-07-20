# AI Debate Multi-Agent Platform

토론 주제를 입력하면 LangGraph 기반 Multi-Agent가 실시간으로 토론을 진행하는 웹 앱.
Planner가 전문가/도구/라운드 수를 정하고, Worker들이 병렬로 토론하며, Aggregate가
요약하고, Judge가 최종 판정을 내린다. 전 과정이 SSE로 프론트에 실시간 스트리밍된다.

## 아키텍처

```
브라우저 (Next.js, :3000)
  └─ POST /debate (SSE) ──▶ FastAPI (:8000)
                              └─ LangGraph
                                   START
                                     ↓
                                  Planner ── LLM이 topic 분석 → workers(role/stance/tools)/rounds 결정
                                     ↓ (Send로 동적 fan-out)
                                  Workers (병렬) ── 각자 Reason → Tool Decision(JSON)
                                     │                → Tool.run() → Observation → Final Answer
                                     │                (Tool 내부에서만 MCP 서버 호출)
                                     ↓
                                  Aggregate ── 발언 요약
                                     ↓
                                  Judge ── Worker(role="judge") 재사용, 전체 토론 검토 후 판정
                                     ↓
                                    END
                              └─ MCP 서버 (:8765) ── search 도구 (worker.py의 SearchTool과 이름 일치)
```

- LLM: Qwen(OpenAI 호환 엔드포인트, NVIDIA 발급 키로 인증) 기본, `NvidiaAPILLM`으로 교체 가능
  (`LLM_PROVIDER` 설정 하나로 전환).
- MCP 서버가 없거나 호출 실패 시 `SearchTool`이 자동으로 Mock 응답으로 폴백 — 데모가 죽지 않는다.

## 폴더 구조

```
backend/      FastAPI + LangGraph 서버
frontend/     Next.js + Tailwind 클라이언트
mcp-server/   Worker의 search tool이 호출하는 실제 MCP 서버
```

## 실행 방법

### 1. MCP 서버

```bash
cd mcp-server
pip install -r requirements.txt
python server.py        # http://localhost:8765/mcp
```

### 2. 백엔드

```bash
cd backend
pip install -r requirements.txt
cp env.example .env     # 값 채우기 (아래 환경변수 참고)
uvicorn app.main:app --reload   # http://localhost:8000
```

**환경변수** (`backend/.env`, `env.example` 참고):

| 변수 | 설명 |
|---|---|
| `LLM_PROVIDER` | `qwen_local`(기본) 또는 `nvidia_api` |
| `QWEN_BASE_URL` | Qwen OpenAI 호환 엔드포인트 |
| `NVIDIA_API_KEY` | NVIDIA(또는 DLI) 발급 API 키 — Qwen 엔드포인트 인증에도 쓰임 |
| `MCP_SERVER_URL` | MCP 서버 주소 (`http://localhost:8765/mcp`). 비워두면 자동 Mock 폴백 |

### 3. 프론트엔드

```bash
cd frontend
npm install
npm run dev              # http://localhost:3000
```

세 개를 모두 띄운 뒤 `http://localhost:3000`에서 토론 주제를 입력하면 된다.

## 주요 구현 포인트

- **Reason → Tool → Observation → Final** 루프: Worker가 LLM으로 도구 필요 여부를 스스로 판단(JSON 응답)하고, 필요할 때만 도구를 호출한다.
- **직접 정의한 Tool**: `SearchTool` — 내부적으로만 MCP를 호출하고, Worker는 `Tool.run()`만 안다(MCP 존재를 모름).
- **멀티에이전트 오케스트레이션**: LangGraph `Send` API로 Planner가 정한 worker 목록을 동적으로 병렬 fan-out.
- **SSE 스트리밍**: Planner → Worker(들) → Aggregate → Judge → 최종 응답이 각각 이벤트로 즉시 전송되어 프론트에 실시간 반영.
- **로딩/에러/재시도**: API 실패 시 빈 화면 대신 에러 배너 + 재시도 버튼을 노출.
