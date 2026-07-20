"use client";

import type { DebateStatus, JudgeResult } from "@/types/debate";

interface JudgePanelProps {
  status: DebateStatus;
  judge: JudgeResult | null;
  scores: Record<string, number>;
}

export default function JudgePanel({ status, judge, scores }: JudgePanelProps) {
  const judging = !judge && (status === "loading" || status === "streaming");
  const mergedScores = { ...scores, ...(judge?.scores ?? {}) };
  const scoreEntries = Object.entries(mergedScores);

  return (
    <aside className="flex w-full flex-col gap-4 rounded-lg border border-black/10 bg-white p-4 text-sm dark:border-white/15 dark:bg-black/40 lg:w-64">
      <div>
        <h2 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Judge 결과
        </h2>
        <p className="flex items-center gap-2">
          {judging && <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />}
          {judge ? "판정 완료" : judging ? "판정 중..." : "대기 중"}
        </p>
        {judge?.verdict && (
          <p className="mt-2 whitespace-pre-wrap rounded-md bg-zinc-50 p-2 text-zinc-800 dark:bg-zinc-900 dark:text-zinc-100">
            {judge.verdict}
          </p>
        )}
      </div>

      <div>
        <h2 className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          승자
        </h2>
        <p className="text-zinc-800 dark:text-zinc-100">{judge?.winner ?? "-"}</p>
      </div>

      <div>
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          점수
        </h2>
        {scoreEntries.length === 0 ? (
          <p className="text-zinc-400 dark:text-zinc-500">-</p>
        ) : (
          <ul className="space-y-1">
            {scoreEntries.map(([name, score]) => (
              <li key={name} className="flex justify-between">
                <span className="text-zinc-600 dark:text-zinc-300">{name}</span>
                <span className="font-medium text-zinc-900 dark:text-zinc-50">{score}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
