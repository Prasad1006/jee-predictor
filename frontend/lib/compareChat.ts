import type { CollegeOption } from "./api";

function collegeFacts(c: CollegeOption): string {
  const lines = [
    `- College: ${c.college_name}`,
    `- Program: ${c.program_name}`,
    `- Closing rank: ${c.closing_rank.toLocaleString()} (${c.tier})`,
    `- Quota: ${c.quota.replace(/_/g, " ")}`,
  ];
  if (c.state) lines.push(`- State: ${c.state}`);
  if (c.recommendation_score != null) lines.push(`- Match score: ${Math.round(c.recommendation_score)}%`);
  if (c.avg_package_inr) lines.push(`- Avg package (DB): ₹${(c.avg_package_inr / 100_000).toFixed(1)} LPA`);
  if (c.rating) lines.push(`- Rating (DB): ${c.rating}`);
  return lines.join("\n");
}

/** User message that asks Gemini for a side-by-side compare inside chat. */
export function buildCompareChatMessage(
  a: CollegeOption,
  b: CollegeOption,
  branch: string,
  studentGoals: string
): string {
  return [
    `Compare these two colleges side by side for ${branch}. Use ONLY our cutoff data for ranks; fill placements, campus, coding culture, fees, ROI from your knowledge where missing.`,
    "",
    "Format your reply exactly like this:",
    "",
    "### 🅰️ " + a.college_name,
    "| Topic | Details |",
    "|---|---|",
    "| Cutoff / chance | ... |",
    "| Placements | ... |",
    "| Coding culture | ... |",
    "| Campus / location | ... |",
    "| Fees / ROI | ... |",
    "",
    "### 🅱️ " + b.college_name,
    "(same table columns)",
    "",
    "### ⚖️ Verdict",
    "One clear pick for me and why (2–3 bullets).",
    "",
    "**College A data:**",
    collegeFacts(a),
    "",
    "**College B data:**",
    collegeFacts(b),
    studentGoals ? `\n**My priorities:** ${studentGoals}` : "",
  ].join("\n");
}
