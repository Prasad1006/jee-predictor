export const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Delhi",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jammu & Kashmir",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Ladakh",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Andaman & Nicobar",
  "Chandigarh",
  "Dadra & Nagar Haveli and Daman & Diu",
  "Puducherry",
] as const;

/** JoSAA counselling years with cutoff data in the database (primary = latest). */
export const CUTOFF_YEARS = [
  { value: 2025, label: "2025 — latest JoSAA" },
  { value: 2024, label: "2024" },
] as const;

export const DEFAULT_CUTOFF_YEAR = 2025;

/** JoSAA uses different rank lists: Main CRL for NIT/IIIT/GFTI, Advanced CRL for IIT. */
export const EXAM_TYPES = [
  { value: "JEE_MAIN", label: "JEE Main (NIT/IIIT/GFTI)", rankLabel: "Main rank" },
  { value: "JEE_ADVANCED", label: "JEE Advanced (IIT)", rankLabel: "Advanced rank" },
] as const;

export type ExamType = (typeof EXAM_TYPES)[number]["value"];
export const DEFAULT_EXAM_TYPE: ExamType = "JEE_MAIN";

export const RANK_TYPES = [
  { value: "CRL", label: "CRL / Common Rank (General)" },
  { value: "CATEGORY", label: "Category Rank (OBC/SC/ST/EWS)" },
] as const;

export type RankType = (typeof RANK_TYPES)[number]["value"];
export const DEFAULT_RANK_TYPE: RankType = "CRL";

export const ROUND_OPTIONS = [
  { value: "LATEST", label: "Latest / Best Available Round" },
  { value: "1", label: "Round 1" },
  { value: "2", label: "Round 2" },
  { value: "3", label: "Round 3" },
  { value: "4", label: "Round 4" },
  { value: "5", label: "Round 5" },
  { value: "6", label: "Round 6" },
] as const;

export const BRANCH_OPTIONS = [
  { value: "ALL", label: "All Branches" },
  { value: "CSE", label: "CSE — Computer Science" },
  { value: "IT", label: "IT — Information Technology" },
  { value: "ECE", label: "ECE — Electronics & Communication" },
  { value: "EEE", label: "EEE — Electrical & Electronics" },
  { value: "EE", label: "EE — Electrical" },
  { value: "ME", label: "ME — Mechanical" },
  { value: "CE", label: "CE — Civil" },
  { value: "CHE", label: "Chemical" },
  { value: "AE", label: "Aerospace" },
  { value: "AI", label: "AI / ML" },
  { value: "DS", label: "Data Science" },
] as const;

export const CATEGORIES = ["GENERAL", "OBC", "SC", "ST", "EWS"] as const;
