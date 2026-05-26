let API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
if (API_BASE && !API_BASE.endsWith("/api/v1") && !API_BASE.endsWith("/api/v1/")) {
  const cleanBase = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  API_BASE = `${cleanBase}/api/v1`;
}


async function throwApiError(res: Response, context: string): Promise<never> {
  const text = await res.text();
  try {
    const json = JSON.parse(text);
    const detail =
      (json && (json.detail || json.error || json.message)) ?? JSON.stringify(json);
    throw new Error(`${context} failed (${res.status}): ${detail}`);
  } catch {
    throw new Error(`${context} failed (${res.status}): ${text || res.statusText}`);
  }
}

export type PredictionResult = {
  rank: number;
  seat_category: string;
  rank_type: string;
  exam_type?: "JEE_MAIN" | "JEE_ADVANCED";
  year: number;
  total_eligible: number;
  /** Full eligible list for sidebar (up to max_results from API). */
  all?: CollegeOption[];
  dream: CollegeOption[];
  target: CollegeOption[];
  safe: CollegeOption[];
  unlikely?: CollegeOption[];
  trace?: Record<string, any>;
  session_id?: string;
};

export type CollegeOption = {
  college_name: string;
  program_name: string;
  branch: string;
  closing_rank: number;
  tier: string;
  quota: string;
  state: string;
  probability_score: number;
  category?: string;
  institute_type?: string;
  college_id?: number;
  program_id?: number;
  recommendation_score?: number;
  why_recommended?: string[];
  rating?: number | null;
  avg_package_inr?: number | null;
  fees_inr?: number | null;
  placement_rate?: number | null;
  ug_fee?: string | null;
};

export type PreferenceChoice = {
  order: number;
  college: string;
  program: string;
  branch: string;
  tier: string;
  closing_rank: number;
  quota: string;
  why: string;
  recommendation_score?: number;
};

export type PreferenceListResult = {
  rank: number;
  seat_category: string;
  year: number;
  total_choices: number;
  strategy: string;
  choices: PreferenceChoice[];
};

export async function predictColleges(body: {
  rank: number;
  category: string;
  gender?: string;
  home_state?: string;
  branch_preferences?: string[];
  year?: number;
  exam_type?: "JEE_MAIN" | "JEE_ADVANCED";
  rank_type?: "CRL" | "CATEGORY";
  round?: string;
  student_goals?: string;
  limit?: number;
  max_results?: number;
}): Promise<PredictionResult> {
  const res = await fetch(`${API_BASE}/predict/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return throwApiError(res, "Predict");
  return res.json();
}

export async function sendChatMessage(body: {
  message: string;
  history?: { role: string; content: string }[];
  rank?: number;
  category?: string;
  home_state?: string;
  branch_preferences?: string[];
  year?: number;
  exam_type?: "JEE_MAIN" | "JEE_ADVANCED";
  rank_type?: "CRL" | "CATEGORY";
  round?: string;
  student_goals?: string;
  focused_college?: string;
  sidebar_colleges?: {
    college_name: string;
    branch: string;
    closing_rank: number;
    tier: string;
  }[];
  session_id?: string;
  selected_card?: {
    college: string;
    branch: string;
    program_name: string;
    closing_rank: number;
    classification: string;
    category?: string;
    round?: string;
  };
}): Promise<{
  reply: string;
  intent: string;
  predictions: PredictionResult | null;
  preference_list?: PreferenceListResult | null;
  verified_cards?: any[];
  context_used: {
    has_predictions: boolean;
    focused_college?: string;
    rag_sources: string[];
    gemini_enabled: boolean;
    gemini_error?: string | null;
    session_info?: {
      session_id: string | null;
      rank: number | null;
      category: string | null;
      exam_type: string | null;
      rank_type: string | null;
      round: string | null;
      total_eligible: number;
    } | null;
  };
}> {
  const res = await fetch(`${API_BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return throwApiError(res, "Chat");
  return res.json();
}

export async function generatePreferenceList(body: {
  rank: number;
  category: string;
  home_state?: string;
  branch_preferences?: string[];
  year?: number;
  exam_type?: "JEE_MAIN" | "JEE_ADVANCED";
  rank_type?: "CRL" | "CATEGORY";
  round?: string;
  student_goals?: string;
  max_choices?: number;
}): Promise<PreferenceListResult> {
  const res = await fetch(`${API_BASE}/preferences/generate/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return throwApiError(res, "Preference list");
  return res.json();
}

export async function fetchMeta(): Promise<{
  categories: string[];
  quotas: string[];
}> {
  const res = await fetch(`${API_BASE}/meta/`);
  if (!res.ok) throw new Error("Failed to load meta");
  return res.json();
}

export type StudentUser = {
  id: number;
  name: string;
  gender: string;
  mobile_number: string;
  created_at: string;
};

export async function registerStudent(body: {
  name: string;
  gender: string;
  mobile_number: string;
}): Promise<StudentUser> {
  const res = await fetch(`${API_BASE}/students/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return throwApiError(res, "Student registration");
  return res.json();
}
