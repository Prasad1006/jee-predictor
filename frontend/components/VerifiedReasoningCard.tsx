"use client";

export type VerifiedCardData = {
  college_name: string;
  program_name: string;
  branch: string;
  user_rank: number;
  closing_rank: number;
  margin: number;
  classification: "SAFE" | "TARGET" | "DREAM" | "UNLIKELY";
  round: string | number;
  category?: string;
  quota?: string;
  reference_cutoff_label?: string;
  cutoff_explanation?: string;
  confidence_level?: string;
  confidence_reason?: string;
  metrics?: {
    tier?: string;
    coding_score?: number;
    placement_score?: number;
    roi_score?: number;
    reputation_score?: number;
    alumni_score?: number;
    campus_score?: number;
  };
};

const tierStyles = {
  SAFE: {
    bg: "bg-emerald-950/15",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    glow: "shadow-[0_0_15px_rgba(16,185,129,0.1)] hover:shadow-[0_0_20px_rgba(16,185,129,0.15)]",
    pulse: "bg-emerald-400",
  },
  TARGET: {
    bg: "bg-amber-950/15",
    border: "border-amber-500/30",
    text: "text-amber-400",
    badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    glow: "shadow-[0_0_15px_rgba(245,158,11,0.1)] hover:shadow-[0_0_20px_rgba(245,158,11,0.15)]",
    pulse: "bg-amber-400",
  },
  DREAM: {
    bg: "bg-violet-950/15",
    border: "border-violet-500/30",
    text: "text-violet-400",
    badge: "bg-violet-500/10 text-violet-400 border-violet-500/20",
    glow: "shadow-[0_0_15px_rgba(139,92,246,0.1)] hover:shadow-[0_0_20px_rgba(139,92,246,0.15)]",
    pulse: "bg-violet-400",
  },
  UNLIKELY: {
    bg: "bg-slate-950/15",
    border: "border-slate-500/30",
    text: "text-slate-400",
    badge: "bg-slate-500/10 text-slate-300 border-slate-500/20",
    glow: "shadow-[0_0_15px_rgba(148,163,184,0.1)] hover:shadow-[0_0_20px_rgba(148,163,184,0.15)]",
    pulse: "bg-slate-400",
  },
};

export function VerifiedReasoningCard({ card }: { card: VerifiedCardData }) {
  const styles = tierStyles[card.classification as keyof typeof tierStyles] || tierStyles.SAFE;
  
  return (
    <div className={`mt-3 rounded-2xl border p-4 transition-all duration-300 ${styles.bg} ${styles.border} ${styles.glow} flex flex-col gap-3.5 backdrop-blur-sm`}>
      {/* Header Badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-slate-900/80 px-2 py-1 rounded-lg border border-slate-800">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${styles.pulse}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${styles.pulse}`}></span>
            </span>
            <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-300">
              Verified DB Truth
            </span>
          </div>
        </div>
        <span className={`rounded-full border px-2.5 py-0.5 text-[9.5px] font-extrabold tracking-wider uppercase shadow-sm ${styles.badge}`}>
          {card.classification}
        </span>
      </div>

      {/* College & Program details */}
      <div>
        <h4 className="text-[13px] font-extrabold text-slate-100 leading-tight">
          {card.college_name}
        </h4>
        <p className="text-[11px] text-slate-400 mt-1 leading-normal font-medium font-sans">
          {card.program_name}
        </p>
      </div>

      {/* Grid containing data points */}
      <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-900/75">
        <div className="flex flex-col gap-0.5">
          <span className="text-[8.5px] font-bold uppercase tracking-wider text-slate-500">Your Rank</span>
          <span className="text-[13px] font-black text-slate-200">{card.user_rank.toLocaleString()}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[8.5px] font-bold uppercase tracking-wider text-slate-500">Closing Rank (Round {card.round})</span>
          <span className="text-[13px] font-black text-slate-200">{card.closing_rank.toLocaleString()}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[8.5px] font-bold uppercase tracking-wider text-slate-500">Rank Margin</span>
          <span className={`text-[13px] font-black ${styles.text}`}>
            {card.margin >= 0 ? `+${card.margin.toLocaleString()}` : `${card.margin.toLocaleString()}`}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[8.5px] font-bold uppercase tracking-wider text-slate-500">Reference cutoff used</span>
          <span className="text-[11px] font-bold text-slate-300 truncate">
            {card.reference_cutoff_label || "Verified cutoff"}
          </span>
        </div>
      </div>

      {card.cutoff_explanation && (
        <div className="rounded-2xl bg-slate-900/80 p-3 border border-slate-800 text-[12px] text-slate-300">
          {card.cutoff_explanation}
        </div>
      )}

      {card.confidence_level && (
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-900/75">
          <div className="flex flex-col gap-0.5">
            <span className="text-[8.5px] font-bold uppercase tracking-wider text-slate-500">Prediction confidence</span>
            <span className="text-[13px] font-black text-slate-200">{card.confidence_level}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[8.5px] font-bold uppercase tracking-wider text-slate-500">Confidence note</span>
            <span className="text-[11px] text-slate-300">{card.confidence_reason}</span>
          </div>
        </div>
      )}

      {card.metrics && (
        <div className="pt-3 border-t border-slate-900/75 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-400">
              Scoring Factors ({card.metrics.tier || "Tier 2"})
            </span>
          </div>
          <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
            {card.metrics.placement_score !== undefined && (
              <div className="bg-slate-950/60 rounded p-1.5 border border-slate-900/40">
                <div className="text-[7.5px] font-bold uppercase tracking-wider text-slate-500">Placement</div>
                <div className="font-extrabold text-slate-200 mt-0.5">{card.metrics.placement_score}/10</div>
              </div>
            )}
            {card.metrics.coding_score !== undefined && (
              <div className="bg-slate-950/60 rounded p-1.5 border border-slate-900/40">
                <div className="text-[7.5px] font-bold uppercase tracking-wider text-slate-500">Coding</div>
                <div className="font-extrabold text-slate-200 mt-0.5">{card.metrics.coding_score}/10</div>
              </div>
            )}
            {card.metrics.roi_score !== undefined && (
              <div className="bg-slate-950/60 rounded p-1.5 border border-slate-900/40">
                <div className="text-[7.5px] font-bold uppercase tracking-wider text-slate-500">ROI</div>
                <div className="font-extrabold text-slate-200 mt-0.5">{card.metrics.roi_score}/10</div>
              </div>
            )}
            {card.metrics.reputation_score !== undefined && (
              <div className="bg-slate-950/60 rounded p-1.5 border border-slate-900/40">
                <div className="text-[7.5px] font-bold uppercase tracking-wider text-slate-500">Reputation</div>
                <div className="font-extrabold text-slate-200 mt-0.5">{card.metrics.reputation_score}/10</div>
              </div>
            )}
            {card.metrics.alumni_score !== undefined && (
              <div className="bg-slate-950/60 rounded p-1.5 border border-slate-900/40">
                <div className="text-[7.5px] font-bold uppercase tracking-wider text-slate-500">Alumni</div>
                <div className="font-extrabold text-slate-200 mt-0.5">{card.metrics.alumni_score}/10</div>
              </div>
            )}
            {card.metrics.campus_score !== undefined && (
              <div className="bg-slate-950/60 rounded p-1.5 border border-slate-900/40">
                <div className="text-[7.5px] font-bold uppercase tracking-wider text-slate-500">Campus Life</div>
                <div className="font-extrabold text-slate-200 mt-0.5">{card.metrics.campus_score}/10</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function VerifiedReasoningCardsList({ cards }: { cards: VerifiedCardData[] | undefined }) {
  if (!cards || cards.length === 0) return null;
  
  return (
    <div className="flex flex-col gap-2.5 mt-1 w-full max-w-full">
      {cards.map((c, i) => (
        <VerifiedReasoningCard key={i} card={c} />
      ))}
    </div>
  );
}
