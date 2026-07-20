// backend/app/graph/worker.py의 _split_expert와 동일한 규칙으로
// "economist_pro" 같은 flat id를 화면에 보여줄 라벨로 바꾼다.

const STAGE_LABELS: Record<string, string> = {
  planner: "Planner",
  aggregate: "사회자 (Aggregate)",
  judge: "Judge",
  final: "최종 응답",
  error: "오류",
};

const ROLE_LABELS: Record<string, string> = {
  economist: "Economist",
  sociologist: "Sociologist",
  political_scientist: "Political Scientist",
  fact_checker: "Fact Checker",
  judge: "Judge",
};

const STANCE_LABELS: Record<string, string> = {
  pro: "찬성",
  con: "반대",
};

function splitExpertId(id: string): [string, string | null] {
  if (id.endsWith("_pro")) return [id.slice(0, -4), "pro"];
  if (id.endsWith("_con")) return [id.slice(0, -4), "con"];
  return [id, null];
}

export function expertLabel(expertId: string): string {
  const [role, stance] = splitExpertId(expertId);
  const roleLabel = ROLE_LABELS[role] ?? role;
  return stance ? `${roleLabel} (${STANCE_LABELS[stance] ?? stance})` : roleLabel;
}

export function stageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? expertLabel(stage);
}
