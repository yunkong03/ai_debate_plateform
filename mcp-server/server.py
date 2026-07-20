"""AI Debate Platform - 팩트체크용 MCP 서버.

Worker(SearchTool)가 호출하는 'search' 도구를 제공한다. 도구 이름은
backend/app/graph/worker.py의 SearchTool.name("search")과 반드시 일치해야 한다.

로컬 실행: python server.py  (HTTP, backend/.env의 MCP_SERVER_URL이 이 주소를 가리킨다)
"""
from fastmcp import FastMCP

mcp = FastMCP("DebateSearchServer")

DOCS = [
    {"title": "기본소득 실증 연구", "body": "핀란드 기본소득 실험(2017-2018)에서 고용률 변화는 미미했으나 삶의 만족도와 정신건강 지표는 개선됐다."},
    {"title": "주 4일제 사례", "body": "영국 4 Day Week 파일럿(2022)에서 참여 기업의 92%가 주 4일제를 유지하기로 했고, 생산성은 유지되거나 소폭 상승했다."},
    {"title": "재택근무와 생산성", "body": "스탠퍼드 Bloom 연구(2023)는 하이브리드 재택근무가 이직률을 낮추고 생산성에는 중립적 영향을 미친다고 보고했다."},
    {"title": "최저임금 인상 효과", "body": "최저임금 인상이 고용에 미치는 영향은 지역·업종에 따라 혼재된 결과를 보이며, 카드-크루거 연구 이후 논쟁이 지속되고 있다."},
    {"title": "탄소세 도입 사례", "body": "스웨덴은 1991년 탄소세를 도입한 이후 배출량은 감소했지만 GDP는 지속 성장해 '디커플링' 사례로 자주 인용된다."},
]


@mcp.tool
def search(query: str, k: int = 2) -> str:
    """토론 주제와 관련된 자료를 키워드 겹침 기준으로 찾아 반환한다 (단어 겹침 · 실무는 임베딩/하이브리드)."""
    scored = sorted(DOCS, key=lambda d: -sum(w in d["body"] for w in query.split()))
    top = scored[:k]
    return "\n".join(f"- {d['title']}: {d['body']}" for d in top)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8765)
