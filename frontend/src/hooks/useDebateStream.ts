"use client";

import { useCallback, useRef, useState } from "react";
import { streamSSE } from "@/lib/sse";
import type {
  DebateEventPayload,
  DebateFinalResponse,
  DebateStatus,
  Evidence,
  JudgeResult,
  Message,
  Plan,
} from "@/types/debate";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface DebateState {
  status: DebateStatus;
  topic: string;
  activeStage: string | null;
  plan: Plan | null;
  messages: Message[];
  evidence: Evidence[];
  scores: Record<string, number>;
  judge: JudgeResult | null;
  finalResponse: DebateFinalResponse | null;
  error: string | null;
}

const INITIAL_STATE: DebateState = {
  status: "idle",
  topic: "",
  activeStage: null,
  plan: null,
  messages: [],
  evidence: [],
  scores: {},
  judge: null,
  finalResponse: null,
  error: null,
};

function applyEvent(prev: DebateState, event: string, payload: DebateEventPayload): DebateState {
  const next: DebateState = { ...prev, status: "streaming", activeStage: event };

  if (payload.messages?.length) next.messages = [...prev.messages, ...payload.messages];
  if (payload.evidence?.length) next.evidence = [...prev.evidence, ...payload.evidence];
  if (payload.scores) next.scores = { ...prev.scores, ...payload.scores };

  if (event === "planner") {
    next.plan = payload.plan ?? prev.plan;
  } else if (event === "judge") {
    next.judge = payload.judge_result ?? prev.judge;
  } else if (event === "final") {
    next.finalResponse = payload as unknown as DebateFinalResponse;
    next.status = "done";
  }

  return next;
}

export function useDebateStream() {
  const [state, setState] = useState<DebateState>(INITIAL_STATE);
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (topic: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState({ ...INITIAL_STATE, status: "loading", topic });

    try {
      const events = streamSSE(`${API_BASE}/debate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
        signal: controller.signal,
      });

      for await (const { event, data } of events) {
        const payload = JSON.parse(data) as DebateEventPayload;

        if (event === "error") {
          setState((prev) => ({
            ...prev,
            status: "error",
            error: payload.message ?? "알 수 없는 오류가 발생했습니다.",
          }));
          return;
        }

        setState((prev) => applyEvent(prev, event, payload));
      }

      setState((prev) => (prev.status === "error" ? prev : { ...prev, status: "done" }));
    } catch (err) {
      if (controller.signal.aborted) return;
      setState((prev) => ({
        ...prev,
        status: "error",
        error: err instanceof Error ? err.message : "네트워크 오류가 발생했습니다.",
      }));
    }
  }, []);

  const retry = useCallback(() => {
    if (state.topic) void run(state.topic);
  }, [run, state.topic]);

  return { state, run, retry };
}
