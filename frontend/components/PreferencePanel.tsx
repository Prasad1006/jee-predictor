"use client";

import type { PreferenceListResult } from "@/lib/api";

const tierEmoji: Record<string, string> = {
  SAFE: "✅",
  TARGET: "🎯",
  DREAM: "🔥",
};

type Props = {
  data: PreferenceListResult | null;
  loading: boolean;
  onClose: () => void;
};

export function PreferencePanel({ data, loading, onClose }: Props) {
  if (!data && !loading) return null;

  return (
    <div className="border-t border-slate-800 bg-gradient-to-b from-[#090911] to-[#0c0c16] p-3 max-h-[38vh] overflow-y-auto text-slate-100">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-bold uppercase tracking-wide text-brand-400">
          📋 JoSAA preference order
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          Hide
        </button>
      </div>

      {loading && (
        <p className="text-sm text-slate-400 animate-pulse">Building your list…</p>
      )}

      {data && !loading && (
        <>
          <p className="text-[10px] text-slate-500 mb-2">
            {data.total_choices} choices · rank {data.rank.toLocaleString()} · {data.seat_category}
          </p>
          <ol className="space-y-2">
            {data.choices.map((c) => (
              <li
                key={c.order}
                className="flex gap-2 rounded-lg border border-slate-800 bg-slate-900/40 p-2 text-xs shadow-sm"
              >
                <span className="font-bold text-slate-500 w-5 shrink-0">{c.order}</span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-slate-100 truncate">
                    {tierEmoji[c.tier] || "•"} {c.college}
                  </p>
                  <p className="text-slate-300 truncate">{c.program}</p>
                  <p className="text-slate-400 mt-0.5">
                    Close ~{c.closing_rank.toLocaleString()} · {c.tier}
                  </p>
                  {c.why && (
                    <p className="text-[10px] text-brand-400 mt-1 italic">{c.why}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
