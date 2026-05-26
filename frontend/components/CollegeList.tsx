import type { CollegeOption } from "@/lib/api";

const tierColors: Record<string, string> = {
  SAFE: "bg-emerald-100 text-emerald-800",
  TARGET: "bg-amber-100 text-amber-800",
  DREAM: "bg-violet-100 text-violet-800",
  UNLIKELY: "bg-slate-100 text-slate-500",
};

export function CollegeList({
  title,
  items,
}: {
  title: string;
  items: CollegeOption[];
}) {
  if (!items.length) return null;
  return (
    <section className="space-y-3">
      <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
      <ul className="space-y-2">
        {items.map((c, i) => (
          <li
            key={`${c.college_name}-${i}`}
            className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium text-slate-900">{c.college_name}</p>
                <p className="text-sm text-slate-600">{c.program_name}</p>
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  tierColors[c.tier] || "bg-slate-100"
                }`}
              >
                {c.tier}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-500">
              Closing rank: <strong>{c.closing_rank}</strong> · {c.quota} ·{" "}
              {c.state || "—"}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
