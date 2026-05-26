"use client";

import { useState } from "react";
import { predictColleges, type PredictionResult } from "@/lib/api";
import { CollegeList } from "./CollegeList";

export function PredictorForm() {
  const [rank, setRank] = useState("18000");
  const [category, setCategory] = useState("OBC");
  const [homeState, setHomeState] = useState("Telangana");
  const [branches, setBranches] = useState("CSE");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PredictionResult | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await predictColleges({
        rank: parseInt(rank, 10),
        category,
        home_state: homeState,
        branch_preferences: branches.split(",").map((b) => b.trim()).filter(Boolean),
        limit: 30,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <form
        onSubmit={onSubmit}
        className="grid gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:grid-cols-2"
      >
        <label className="block text-sm">
          <span className="font-medium text-slate-700">JEE Rank</span>
          <input
            type="number"
            value={rank}
            onChange={(e) => setRank(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            required
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-slate-700">Category</span>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          >
            {["GENERAL", "OBC", "SC", "ST", "EWS"].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium text-slate-700">Home state</span>
          <input
            type="text"
            value={homeState}
            onChange={(e) => setHomeState(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium text-slate-700">Branch preferences (comma-separated)</span>
          <input
            type="text"
            value={branches}
            onChange={(e) => setBranches(e.target.value)}
            placeholder="CSE, ECE"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="sm:col-span-2 rounded-lg bg-brand-600 py-2.5 font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Predicting…" : "Predict colleges"}
        </button>
      </form>

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
      )}

      {result && (
        <div className="space-y-8">
          <p className="text-slate-600">
            Found <strong>{result.total_eligible}</strong> eligible options for rank{" "}
            <strong>{result.rank.toLocaleString()}</strong> ({result.seat_category}).
          </p>
          {result.total_eligible === 0 ? (
            <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900">
              No matches for this branch filter. Try broader branches (e.g. CSE maps to Computer
              Science) or clear branch preferences.
            </p>
          ) : (
            <>
              <CollegeList title="Safe — strong backup" items={result.safe} />
              <CollegeList title="Target — realistic" items={result.target} />
              <CollegeList title="Dream — borderline" items={result.dream} />
              {result.unlikely && result.unlikely.length > 0 && (
                <CollegeList title="Unlikely — unrealistic" items={result.unlikely} />
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
