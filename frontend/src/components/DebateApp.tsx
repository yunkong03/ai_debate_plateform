"use client";

import { useDebateStream } from "@/hooks/useDebateStream";
import PlannerPanel from "@/components/PlannerPanel";
import JudgePanel from "@/components/JudgePanel";
import EvidencePanel from "@/components/EvidencePanel";
import DebateLog from "@/components/DebateLog";
import ChatInput from "@/components/ChatInput";
import StatusBanner from "@/components/StatusBanner";

export default function DebateApp() {
  const { state, run, retry } = useDebateStream();

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-4 p-4">
      <header>
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">AI Debate Platform</h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          토론 주제를 입력하면 Planner → Worker → Judge 순서로 실시간 진행 상황을 볼 수 있습니다.
        </p>
      </header>

      <StatusBanner
        status={state.status}
        activeStage={state.activeStage}
        error={state.error}
        onRetry={retry}
      />

      <div className="flex flex-1 flex-col gap-4 lg:flex-row">
        <PlannerPanel status={state.status} plan={state.plan} />

        <div className="flex flex-1 flex-col gap-3">
          <ChatInput status={state.status} onSubmit={run} />
          <DebateLog topic={state.topic} messages={state.messages} />
        </div>

        <JudgePanel status={state.status} judge={state.judge} scores={state.scores} />
      </div>

      <EvidencePanel evidence={state.evidence} />
    </div>
  );
}
