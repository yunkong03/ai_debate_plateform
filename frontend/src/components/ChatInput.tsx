"use client";

import { useState } from "react";
import type { DebateStatus } from "@/types/debate";

interface ChatInputProps {
  status: DebateStatus;
  onSubmit: (topic: string) => void;
}

export default function ChatInput({ status, onSubmit }: ChatInputProps) {
  const [value, setValue] = useState("");
  const busy = status === "loading" || status === "streaming";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const topic = value.trim();
    if (!topic || busy) return;
    onSubmit(topic);
    setValue("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="토론 주제를 입력하세요 (예: 기본소득 도입)"
        disabled={busy}
        className="flex-1 rounded-lg border border-black/10 bg-white px-4 py-2 text-sm outline-none focus:border-blue-400 disabled:opacity-60 dark:border-white/15 dark:bg-black"
      />
      <button
        type="submit"
        disabled={busy || !value.trim()}
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "진행 중..." : "토론 시작"}
      </button>
    </form>
  );
}
