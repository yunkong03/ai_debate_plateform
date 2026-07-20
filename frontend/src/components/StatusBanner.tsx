"use client";

import type { DebateStatus } from "@/types/debate";
import { stageLabel } from "@/lib/labels";

interface StatusBannerProps {
  status: DebateStatus;
  activeStage: string | null;
  error: string | null;
  onRetry: () => void;
}

export default function StatusBanner({ status, activeStage, error, onRetry }: StatusBannerProps) {
  if (status === "error") {
    return (
      <div className="flex items-center justify-between gap-3 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
        <span>⚠ {error ?? "오류가 발생했습니다."}</span>
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 rounded-md bg-red-600 px-3 py-1 font-medium text-white hover:bg-red-700"
        >
          다시 시도
        </button>
      </div>
    );
  }

  if (status === "loading" || status === "streaming") {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-200">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <span>
          {activeStage ? `${stageLabel(activeStage)} 진행 중...` : "연결 중..."}
        </span>
      </div>
    );
  }

  if (status === "done") {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200">
        ✓ 토론이 종료되었습니다.
      </div>
    );
  }

  return null;
}
