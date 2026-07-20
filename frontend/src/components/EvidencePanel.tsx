"use client";

import type { Evidence } from "@/types/debate";
import { expertLabel } from "@/lib/labels";

interface EvidencePanelProps {
  evidence: Evidence[];
}

export default function EvidencePanel({ evidence }: EvidencePanelProps) {
  return (
    <section className="w-full rounded-lg border border-black/10 bg-white p-4 text-sm dark:border-white/15 dark:bg-black/40">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        Evidence
      </h2>
      {evidence.length === 0 ? (
        <p className="text-zinc-400 dark:text-zinc-500">아직 수집된 근거가 없습니다.</p>
      ) : (
        <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {evidence.map((e, i) => (
            <li
              key={`${e.round}-${e.speaker}-${i}`}
              className="rounded-md border border-black/10 bg-zinc-50 p-2 dark:border-white/10 dark:bg-zinc-900"
            >
              <div className="mb-1 text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                {expertLabel(e.speaker)} · {e.source} · Round {e.round}
              </div>
              <div className="whitespace-pre-wrap text-zinc-800 dark:text-zinc-100">{e.content}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
