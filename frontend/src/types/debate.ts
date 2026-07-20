// backend/app/graph/state.py, backend/app/core/schemas.py 와 형태를 맞춘 타입들.

export interface Message {
  round: number;
  speaker: string;
  content: string;
}

export interface Evidence {
  round: number;
  speaker: string;
  source: string;
  content: string;
}

export interface WorkerSpec {
  role: string;
  stance?: string | null;
  tools?: string[];
}

export interface Plan {
  topic?: string;
  workers?: WorkerSpec[];
  rounds?: number;
}

export interface JudgeResult {
  verdict?: string;
  winner?: string;
  scores?: Record<string, number>;
}

export interface DebateFinalResponse {
  topic: string;
  experts: string[];
  rounds: number;
  opinions: { expert: string; content: string }[];
  summary?: string | null;
  verdict?: string | null;
}

export type DebateStatus = "idle" | "loading" | "streaming" | "done" | "error";

// planner_node/worker_node/judge_node 등이 반환하는 partial DebateState.
// SSE data 페이로드가 그대로 이 모양으로 온다.
export interface DebateEventPayload {
  plan?: Plan;
  workers?: string[];
  messages?: Message[];
  evidence?: Evidence[];
  scores?: Record<string, number>;
  judge_result?: JudgeResult;
  current_round?: number;
  max_round?: number;
  message?: string; // event: error 일 때
  [key: string]: unknown;
}
