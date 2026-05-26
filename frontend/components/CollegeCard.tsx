"use client";

import type { CollegeOption } from "@/lib/api";

const tierColors: Record<string, string> = {
  SAFE: "bg-emerald-950/50 text-emerald-400 border-emerald-500/20",
  TARGET: "bg-amber-950/50 text-amber-400 border-amber-500/20",
  DREAM: "bg-violet-950/50 text-violet-400 border-violet-500/20",
  UNLIKELY: "bg-slate-950/50 text-slate-400 border-slate-800",
};

type Props = {
  college: CollegeOption;
  selected: boolean;
  expanded: boolean;
  onToggleWhy: () => void;
  onSelect: () => void;
};

export function CollegeCard({
  college,
  selected,
  expanded,
  onToggleWhy,
  onSelect,
}: Props) {
  const isIIT = college.college_name.toLowerCase().includes("iit") && !college.college_name.toLowerCase().includes("iiit");
  const isIIIT = college.college_name.toLowerCase().includes("iiit");
  const isNIT = college.college_name.toLowerCase().includes("nit");

  let badgeLabel = "COL";
  let badgeColor = "bg-slate-900/60 text-slate-400 border-slate-800/80 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]";
  
  if (isIIT) {
    badgeLabel = "IIT";
    badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_8px_rgba(245,158,11,0.05)]";
  } else if (isIIIT) {
    badgeLabel = "IIIT";
    badgeColor = "bg-violet-500/10 text-violet-400 border-violet-500/20 shadow-[0_0_8px_rgba(139,92,246,0.05)]";
  } else if (isNIT) {
    badgeLabel = "NIT";
    badgeColor = "bg-cyan-500/10 text-cyan-400 border-cyan-500/20 shadow-[0_0_8px_rgba(6,182,212,0.05)]";
  }

  return (
    <div
      onClick={onSelect}
      className={`group relative overflow-hidden rounded-2xl border p-4 transition-all duration-300 backdrop-blur-sm cursor-pointer select-none ${
        selected
          ? "border-brand-500 bg-slate-900/90 shadow-[0_4px_20px_rgba(59,130,246,0.12)] ring-1 ring-brand-500/30 text-slate-100"
          : "border-slate-800/60 bg-slate-950/40 hover:border-slate-700/80 hover:bg-slate-900/40 text-slate-300 hover:shadow-md hover:scale-[1.01]"
      }`}
    >
      <div className="flex gap-3">
        {/* Customized Logo / Badge indicator for Institute Type */}
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border text-[9px] font-black tracking-widest ${badgeColor}`}>
          {badgeLabel}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className={`text-[13px] font-extrabold leading-snug tracking-tight truncate ${selected ? "text-slate-100" : "text-slate-200 group-hover:text-slate-100"}`}>
              {college.college_name}
            </h4>
            <span
              className={`shrink-0 rounded-full border px-2 py-0.5 text-[8.5px] font-black tracking-wider uppercase ${
                tierColors[college.tier] || "bg-slate-800 text-slate-400 border-slate-700"
              }`}
            >
              {college.tier}
            </span>
          </div>

          <p className="mt-1 text-[11px] text-slate-400 line-clamp-2 leading-relaxed font-sans font-medium">
            {college.program_name}
          </p>

          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
            <div>
              Close: <strong className="text-slate-300 font-extrabold">{college.closing_rank.toLocaleString()}</strong>
            </div>
            {college.state && (
              <div className="flex items-center gap-1">
                <span className="h-1 w-1 rounded-full bg-slate-700"></span>
                <span>{college.state}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-3.5 border-t border-slate-900/65 pt-2.5 flex gap-2">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onToggleWhy();
          }}
          className="flex-1 rounded-xl bg-slate-950/40 hover:bg-slate-900 py-1.5 text-[9.5px] font-bold text-slate-400 hover:text-slate-200 border border-slate-800/80 transition active:scale-[0.98] cursor-pointer"
        >
          {expanded ? "Hide reason" : "Why recommended?"}
        </button>
      </div>

      {expanded && college.why_recommended && college.why_recommended.length > 0 && (
        <ul className="mt-2.5 space-y-1.5 rounded-xl bg-brand-950/20 border border-brand-900/30 p-3 text-[10.5px] text-brand-300 leading-normal animate-in fade-in slide-in-from-top-1 duration-200">
          {college.why_recommended.map((w, i) => (
            <li key={i} className="flex items-start gap-1.5">
              <span className="text-brand-400 font-bold">✔</span>
              <span>{w}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

