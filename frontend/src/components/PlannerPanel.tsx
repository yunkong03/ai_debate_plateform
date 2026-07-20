"use client";

import type { DebateStatus, Plan } from "@/types/debate";

interface PlannerPanelProps {
  status: DebateStatus;
  plan: Plan | null;
}

export default function PlannerPanel({ status, plan }: PlannerPanelProps) {
  const plannerDone = Boolean(plan);
  const plannerRunning = !plannerDone && (status === "loading" || status === "streaming");

  return (
    <aside className="flex w-full flex-col gap-4 rounded-lg border border-black/10 bg-white p-4 text-sm dark:border-white/15 dark:bg-black/40 lg:w-64">
      <div>
        <h2 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Planner 상태
        </h2>
        <p className="flex items-center gap-2">
          {plannerRunning && (
            <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
          )}
          {plannerDone ? "계획 수립 완료" : plannerRunning ? "분석 중..." : "대기 중"}
        </p>
        {plan?.rounds !== undefined && (
          <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">라운드 수: {plan.rounds}</p>
        )}
      </div>

      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          선택된 전문가
        </h2>
        {!plan?.workers?.length ? (
          <p className="text-zinc-400 dark:text-zinc-500">아직 없음</p>
        ) : (
          <ul className="space-y-1.5">
            {plan.workers.map((w, i) => (
              <li
                key={`${w.role}-${w.stance ?? "none"}-${i}`}
                className="flex items-center justify-between rounded-md bg-zinc-50 px-2 py-1.5 dark:bg-zinc-900"
              >
                <span className="font-medium text-zinc-800 dark:text-zinc-100">
                  {w.role}
                  {w.stance ? ` (${w.stance})` : ""}
                </span>
                {w.tools?.length ? (
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {w.tools.join(", ")}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
