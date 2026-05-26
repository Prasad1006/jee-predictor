import type { CollegeOption } from "./api";

export type InstituteFilter = "ALL" | "IIT" | "NIT" | "IIIT" | "GFTI";
export type TierFilter = "ALL" | "SAFE" | "TARGET" | "DREAM" | "UNLIKELY";
export type StateFilter = string; // "ALL" or state name
export type BranchFilter = string; // "ALL" or branch name

/** Normalize state strings for comparison (Tamil nadu → tamil nadu). */
export function normalizeStateName(state: string): string {
  return state.trim().toLowerCase().replace(/\s+/g, " ");
}

/** Infer IIT / NIT / IIIT from API college category or name. */
export function getInstituteType(c: CollegeOption): InstituteFilter {
  const cat = (c.institute_type || c.category || "").toUpperCase().trim();
  if (cat === "IIT") return "IIT";
  if (cat === "NIT") return "NIT";
  if (cat === "IIIT") return "IIIT";
  if (cat === "GFTI") return "GFTI";
  if (cat === "DEEMED" || cat === "OTHER" || cat === "") {
    // fall through to name
  }

  const name = c.college_name.toUpperCase();
  if (name.includes("INDIAN INSTITUTE OF TECHNOLOGY") || /\bIIT[\s,]/.test(name) || name.startsWith("IIT ")) {
    return "IIT";
  }
  if (
    name.includes("INDIAN INSTITUTE OF INFORMATION TECHNOLOGY")
    || name.includes("IIIT")
    || /\bIIIT\s/.test(name)
  ) {
    return "IIIT";
  }
  if (
    name.includes("NATIONAL INSTITUTE OF TECHNOLOGY")
    || /\bNIT[\s,]/.test(name)
    || name.startsWith("NIT ")
  ) {
    return "NIT";
  }

  return "GFTI";
}

/** Unique non-empty states from a college list, sorted A–Z. */
export function uniqueStatesFromColleges(colleges: CollegeOption[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const c of colleges) {
    const s = (c.state || "").trim();
    if (!s) continue;
    const key = normalizeStateName(s);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
  }
  return out.sort((a, b) => a.localeCompare(b));
}

/** Get normalized user-friendly branch based on program name and canonical branch. */
export function getNormalizedBranch(c: CollegeOption): string {
  const name = (c.program_name || "").toUpperCase();
  const branchVal = (c.branch || "").toUpperCase();

  if (name.includes("COMPUTER SCIENCE") || name.includes("COMPUTER ENGINEERING") || name.includes("CSE")) {
    return "Computer Science (CSE)";
  }
  if (name.includes("INFORMATION TECHNOLOGY") || name.includes("IT")) {
    return "Information Technology (IT)";
  }
  if (name.includes("ELECTRONICS AND COMMUNICATION") || name.includes("ELECTRONICS & COMMUNICATION") || name.includes("ECE")) {
    return "Electronics & Communication (ECE)";
  }
  if (name.includes("ELECTRICAL AND ELECTRONICS") || name.includes("ELECTRICAL & ELECTRONICS") || name.includes("EEE")) {
    return "Electrical & Electronics (EEE)";
  }
  if (name.includes("ELECTRICAL ENGINEERING") || name.includes("ELECTRICAL") || branchVal === "EE" || branchVal === "ELECTRICAL_ENGINEERING") {
    return "Electrical (EE)";
  }
  if (name.includes("MECHANICAL ENGINEERING") || name.includes("MECHANICAL") || branchVal === "ME" || branchVal === "MECHANICAL_ENGINEERING") {
    return "Mechanical (ME)";
  }
  if (name.includes("CIVIL ENGINEERING") || name.includes("CIVIL") || branchVal === "CE" || branchVal === "CIVIL_ENGINEERING") {
    return "Civil (CE)";
  }
  if (name.includes("CHEMICAL") || branchVal === "CHE" || branchVal === "CHEMICAL_ENGINEERING") {
    return "Chemical";
  }
  if (name.includes("AEROSPACE") || branchVal === "AE" || branchVal === "AEROSPACE_ENGINEERING") {
    return "Aerospace";
  }
  if (name.includes("ARTIFICIAL INTELLIGENCE") || name.includes("AI") || name.includes("MACHINE LEARNING") || branchVal === "AI") {
    return "Artificial Intelligence / ML";
  }
  if (name.includes("DATA SCIENCE") || branchVal === "DS") {
    return "Data Science";
  }

  // Fallback to formatting branchVal
  if (branchVal) {
    return branchVal
      .replace(/_/g, " ")
      .split(" ")
      .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
      .join(" ");
  }

  return "Others";
}

/** Unique non-empty branches from a college list, sorted A–Z. */
export function uniqueBranchesFromColleges(colleges: CollegeOption[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const c of colleges) {
    const b = getNormalizedBranch(c);
    if (!b) continue;
    const key = b.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(b);
  }
  return out.sort((a, b) => a.localeCompare(b));
}

export function filterColleges(
  colleges: CollegeOption[],
  options: {
    search: string;
    tier: TierFilter;
    institute: InstituteFilter;
    state: StateFilter;
    branch: BranchFilter;
  }
): CollegeOption[] {
  let list = colleges;

  if (options.tier !== "ALL") {
    list = list.filter((c) => c.tier === options.tier);
  }

  if (options.institute !== "ALL") {
    list = list.filter((c) => getInstituteType(c) === options.institute);
  }

  if (options.state !== "ALL") {
    const want = normalizeStateName(options.state);
    list = list.filter((c) => normalizeStateName(c.state || "") === want);
  }

  if (options.branch !== "ALL") {
    const want = options.branch.toLowerCase();
    list = list.filter((c) => getNormalizedBranch(c).toLowerCase() === want);
  }

  const raw = options.search.trim().toLowerCase();
  if (raw) {
    const tokens = raw.split(/\s+/).filter(Boolean);
    list = list.filter((c) => {
      const haystack = [
        c.college_name,
        c.program_name,
        c.branch,
        c.state,
        c.quota,
      ]
        .join(" ")
        .toLowerCase();
      return tokens.every((t) => haystack.includes(t));
    });
  }

  return list;
}

export const INSTITUTE_FILTERS: { id: InstituteFilter; label: string }[] = [
  { id: "ALL", label: "All" },
  { id: "IIT", label: "IIT" },
  { id: "NIT", label: "NIT" },
  { id: "IIIT", label: "IIIT" },
  { id: "GFTI", label: "GFTI" },
];
