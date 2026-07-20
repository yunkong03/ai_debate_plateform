"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/types/debate";
import { expertLabel } from "@/lib/labels";

interface DebateLogProps {
  topic: string;
  messages: Message[];
}

export default function DebateLog({ topic, messages }: DebateLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, topic]);

  return (
    <div className="flex-1 space-y-3 overflow-y-auto rounded-lg border border-black/10 bg-white p-4 dark:border-white/15 dark:bg-black/40">
      {!topic && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          토론 주제를 입력하면 여기에 진행 로그가 표시됩니다.
        </p>
      )}

      {topic && (
        <div className="ml-auto max-w-[80%] rounded-lg rounded-tr-none bg-blue-600 px-3 py-2 text-sm text-white">
          {topic}
        </div>
      )}

      {messages.map((m, i) => (
        <div
          key={`${m.round}-${m.speaker}-${i}`}
          className="max-w-[85%] rounded-lg rounded-tl-none border border-black/10 bg-zinc-50 px-3 py-2 text-sm dark:border-white/10 dark:bg-zinc-900"
        >
          <div className="mb-1 text-xs font-semibold text-zinc-500 dark:text-zinc-400">
            {expertLabel(m.speaker)} · Round {m.round}
          </div>
          <div className="whitespace-pre-wrap text-zinc-900 dark:text-zinc-100">{m.content}</div>
        </div>
      ))}

      <div ref={bottomRef} />
    </div>
  );
}
