"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { CollegeOption, PredictionResult } from "@/lib/api";
import { CollegeCard } from "./CollegeCard";
import { listKey, rowId } from "@/lib/collegeKeys";
import {
  filterColleges,
  INSTITUTE_FILTERS,
  uniqueStatesFromColleges,
  type InstituteFilter,
  type StateFilter,
  type TierFilter,
} from "@/lib/collegeFilters";

const tierColors: Record<string, string> = {
  SAFE: "bg-emerald-100 text-emerald-800 border-emerald-200",
  TARGET: "bg-amber-100 text-amber-800 border-amber-200",
  DREAM: "bg-violet-100 text-violet-800 border-violet-200",
  UNLIKELY: "bg-slate-100 text-slate-600 border-slate-200",
};

const DUMMY_COLLEGES: CollegeOption[] = [
  {
    college_id: -1,
    college_name: "IIT Bombay",
    program_id: -1,
    program_name: "Computer Science and Engineering (4 Years, Bachelor of Technology)",
    branch: "CSE",
    closing_rank: 67,
    tier: "DREAM",
    quota: "AI",
    state: "Maharashtra",
    probability_score: 0.95,
    why_recommended: ["Top ranking institute in India", "Exceptional coding culture & placements"],
  },
  {
    college_id: -2,
    college_name: "NIT Trichy",
    program_id: -2,
    program_name: "Electronics and Communication Engineering (4 Years, Bachelor of Technology)",
    branch: "ECE",
    closing_rank: 3200,
    tier: "TARGET",
    quota: "OS",
    state: "Tamil Nadu",
    probability_score: 0.85,
    why_recommended: ["Highest placement rate among NITs", "Strong alumni network"],
  },
  {
    college_id: -3,
    college_name: "IIIT Allahabad",
    program_id: -3,
    program_name: "Information Technology (4 Years, Bachelor of Technology)",
    branch: "IT",
    closing_rank: 4800,
    tier: "SAFE",
    quota: "AI",
    state: "Uttar Pradesh",
    probability_score: 0.75,
    why_recommended: ["Industry-leading average package", "Strong coding culture"],
  }
];

type Props = {
  result: PredictionResult | null;
  loading: boolean;
  selectedKey: string | null;
  onSelect: (college: CollegeOption) => void;
  filter: TierFilter;
  onFilterChange: (f: TierFilter) => void;
};

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-2.5 py-1 text-[10px] font-semibold transition ${
        active
          ? "bg-brand-600 text-white shadow-sm"
          : "bg-slate-900 text-slate-400 hover:bg-slate-800"
      }`}
    >
      {children}
    </button>
  );
}

export function CollegeSidebar({
  result,
  loading,
  selectedKey,
  onSelect,
  filter,
  onFilterChange,
}: Props) {
  const [search, setSearch] = useState("");
  const [instituteFilter, setInstituteFilter] = useState<InstituteFilter>("ALL");
  const [stateFilter, setStateFilter] = useState<StateFilter>("ALL");
  const [expandedWhy, setExpandedWhy] = useState<string | null>(null);

  useEffect(() => {
    setSearch("");
    setInstituteFilter("ALL");
    setStateFilter("ALL");
    setExpandedWhy(null);
  }, [result]);

  const allColleges = useMemo(() => {
    if (!result) return [];
    if (result.all && result.all.length > 0) return result.all;
    return [...result.safe, ...result.target, ...result.dream];
  }, [result]);

  const instituteFilterOptions = useMemo(() => {
    if (result?.rank_type === "JEE_ADVANCED") {
      return INSTITUTE_FILTERS.filter((f) => f.id === "ALL" || f.id === "IIT");
    }
    return INSTITUTE_FILTERS.filter((f) => f.id !== "IIT");
  }, [result?.rank_type]);

  const stateOptions = useMemo(
    () => uniqueStatesFromColleges(allColleges),
    [allColleges]
  );

  const rankTypeLabel =
    result?.rank_type === "JEE_ADVANCED"
      ? "JEE Advanced · IIT"
      : "JEE Main · NIT / IIIT / GFTI";

  const items = useMemo(
    () =>
      filterColleges(allColleges, {
        search,
        tier: filter,
        institute: instituteFilter,
        state: stateFilter,
        branch: "ALL",
      }),
    [allColleges, search, filter, instituteFilter, stateFilter]
  );

  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-800/80 bg-[#08080d]/90 text-slate-200">
      <div className="border-b border-slate-800/80 bg-slate-950/60 px-3 py-3 space-y-2.5">
        <div>
          <h2 className="text-sm font-bold text-slate-100">Your colleges</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {result
              ? `${rankTypeLabel} · JoSAA ${result.year} · ${result.total_eligible} options`
              : "Pick rank type, then Predict"}
          </p>
        </div>

        {result && (
          <>
            <div className="relative">
              <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </span>
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search college, branch, city…"
                className="w-full rounded-lg border border-slate-800 bg-slate-900/60 py-2 pl-9 pr-8 text-sm text-slate-100 placeholder:text-slate-500 focus:border-brand-500 focus:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>

            <div>
              <p className="text-[10px] font-medium uppercase text-slate-400 mb-1">Institute</p>
              <div className="flex flex-wrap gap-1">
                {instituteFilterOptions.map(({ id, label }) => (
                  <FilterChip
                    key={id}
                    active={instituteFilter === id}
                    onClick={() => setInstituteFilter(id)}
                  >
                    {label}
                  </FilterChip>
                ))}
              </div>
            </div>

            {stateOptions.length > 0 && (
              <div>
                <p className="text-[10px] font-medium uppercase text-slate-400 mb-1">State</p>
                <select
                  value={stateFilter}
                  onChange={(e) => setStateFilter(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900/60 px-2 py-1.5 text-xs text-slate-200 focus:border-brand-500 focus:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                >
                  <option value="ALL">All states</option>
                  {stateOptions.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            )}



            <div>
              <p className="text-[10px] font-medium uppercase text-slate-400 mb-1">Chance</p>
              <div className="flex flex-wrap gap-1">
                {(["ALL", "SAFE", "TARGET", "DREAM", "UNLIKELY"] as const).map((f) => (
                  <FilterChip
                    key={f}
                    active={filter === f}
                    onClick={() => onFilterChange(f)}
                  >
                    {f === "ALL" ? "All" : f.charAt(0) + f.slice(1).toLowerCase()}
                  </FilterChip>
                ))}
              </div>
            </div>

            <p className="text-[10px] text-slate-500">
              Showing <strong>{items.length}</strong> of {allColleges.length}
              {result && result.total_eligible > allColleges.length && (
                <> · {result.total_eligible.toLocaleString()} total eligible</>
              )}
            </p>
          </>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading && (
          <p className="text-center text-sm text-slate-400 py-8 animate-pulse">
            Finding colleges…
          </p>
        )}
        {!loading && !result && (
          <div className="space-y-4">
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/10 p-4 text-center text-xs text-slate-400">
              Fill parameters above and click <strong className="text-slate-200">Predict</strong> to get personalized matching colleges.
            </div>
            
            <div className="pt-1.5" id="tour-college-list">
              <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 mb-2.5 px-1 flex items-center gap-1.5">
                <span className="flex h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse"></span>
                <span>💡 Example Colleges (Click to query AI):</span>
              </p>
              <div className="space-y-2">
                {DUMMY_COLLEGES.map((c, i) => {
                  const key = `dummy-${i}`;
                  const selected = selectedKey === rowId(c);
                  return (
                    <CollegeCard
                      key={key}
                      college={c}
                      selected={selected}
                      expanded={expandedWhy === key}
                      onToggleWhy={() => setExpandedWhy(expandedWhy === key ? null : key)}
                      onSelect={() => onSelect(c)}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        )}
        {!loading && result && items.length === 0 && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/10 p-5 text-center text-sm text-slate-400">
            No colleges match your search.
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setInstituteFilter("ALL");
                setStateFilter("ALL");
                onFilterChange("ALL");
              }}
              className="mt-2 block w-full text-brand-400 text-xs font-medium hover:underline"
            >
              Clear all filters
            </button>
          </div>
        )}
        {!loading &&
          items.map((c, i) => {
            const key = listKey(c, i);
            const selected = selectedKey === rowId(c);
            return (
              <CollegeCard
                key={key}
                college={c}
                selected={selected}
                expanded={expandedWhy === key}
                onToggleWhy={() => setExpandedWhy(expandedWhy === key ? null : key)}
                onSelect={() => onSelect(c)}
              />
            );
          })}
      </div>
    </aside>
  );
}

export { rowId as collegeKey };
