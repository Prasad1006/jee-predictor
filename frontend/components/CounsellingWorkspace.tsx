"use client";

import { useRef, useState, useMemo, lazy, Suspense, useEffect } from "react";
import {
  generatePreferenceList,
  predictColleges,
  sendChatMessage,
  registerStudent,
  type CollegeOption,
  type PreferenceListResult,
  type PredictionResult,
} from "@/lib/api";
import {
  BRANCH_OPTIONS,
  CATEGORIES,
  CUTOFF_YEARS,
  DEFAULT_CUTOFF_YEAR,
  DEFAULT_RANK_TYPE,
  INDIAN_STATES,
  RANK_TYPES,
  EXAM_TYPES,
  DEFAULT_EXAM_TYPE,
  ROUND_OPTIONS,
  type RankType,
  type ExamType,
} from "@/lib/constants";
import { CollegeSidebar } from "./CollegeSidebar";
import { MarkdownMessage } from "./MarkdownMessage";
import { rowId } from "@/lib/collegeKeys";
import { VerifiedReasoningCardsList, type VerifiedCardData } from "./VerifiedReasoningCard";

// Lazy load PreferencePanel to reduce initial bundle
const PreferencePanel = lazy(() => import("./PreferencePanel").then(m => ({ default: m.PreferencePanel })));

const SEO_PAGES = [
  "best colleges under 10k rank",
  "best NITs for CSE",
  "IIIT Allahabad vs NIT Trichy",
  "NIT mech vs iiit cse",
  "best colleges for 20k rank",
  "ECE vs CSE",
  "JoSAA choice filling order",
];

type Message = { role: "user" | "model"; content: string; verified_cards?: VerifiedCardData[] };

export function CounsellingWorkspace() {
  const [rank, setRank] = useState("");
  const [category, setCategory] = useState("OBC");
  const [homeState, setHomeState] = useState("Andhra Pradesh");
  const [branch, setBranch] = useState("CSE");
  const [cutoffYear, setCutoffYear] = useState(DEFAULT_CUTOFF_YEAR);
  const [examType, setExamType] = useState<ExamType>(DEFAULT_EXAM_TYPE);
  const [rankType, setRankType] = useState<RankType>(DEFAULT_RANK_TYPE);
  const [round, setRound] = useState("LATEST");
  const [studentGoals, setStudentGoals] = useState("");
  const [preferenceList, setPreferenceList] = useState<PreferenceListResult | null>(null);
  const [prefLoading, setPrefLoading] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);

  const [sessionId, setSessionId] = useState<string>("");
  const [sessionInfo, setSessionInfo] = useState<{
    rank: number;
    category: string;
    exam_type: string;
    round: string;
    total_eligible: number;
  } | null>(null);

  const [isParamBarExpanded, setIsParamBarExpanded] = useState(true);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);
  const [tourStep, setTourStep] = useState<number>(-1);
  const [activeMobileTab, setActiveMobileTab] = useState<"colleges" | "chat">("chat");

  // Auto-start guided tour for first-time visitors
  useEffect(() => {
    if (typeof window !== "undefined") {
      const tourSeen = localStorage.getItem("hasSeenTour_v3");
      if (!tourSeen) {
        setTimeout(() => setTourStep(0), 1200);
      }
    }
  }, []);

  // Sync expansions and values with tour steps
  useEffect(() => {
    if (tourStep === 1) {
      setIsParamBarExpanded(true);
    } else if (tourStep === 2 || tourStep === 3 || tourStep === 4) {
      setIsSidebarExpanded(true);
    }

    if (tourStep === 3) {
      setInput("📍 NIT Trichy (Target) - Computer Science and Engineering | Tell me: placements, package, campus culture. Should I pick it?");
    } else if (tourStep === 5) {
      setInput("NIT mech vs iiit cse");
    } else if (tourStep === -1) {
      // Clear input when tour completes/closes to prevent leftover state
      setInput((prev) => {
        if (prev.startsWith("📍 NIT Trichy") || prev === "NIT mech vs iiit cse") {
          return "";
        }
        return prev;
      });
    }
  }, [tourStep]);

  // Memoize to prevent unnecessary recalculations
  const examTypeMeta = useMemo(
    () => EXAM_TYPES.find((e) => e.value === examType) ?? EXAM_TYPES[0],
    [examType]
  );
  const rankTypeMeta = useMemo(
    () => RANK_TYPES.find((r) => r.value === rankType) ?? RANK_TYPES[0],
    [rankType]
  );

  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [predictLoading, setPredictLoading] = useState(false);
  const [sidebarFilter, setSidebarFilter] = useState<"ALL" | "SAFE" | "TARGET" | "DREAM" | "UNLIKELY">("ALL");
  const [selectedCollege, setSelectedCollege] = useState<CollegeOption | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "model",
      content:
        "Welcome! Ask me anything about placements, campus culture, cutoffs, or preference strategies.\n\n**Example queries:**\n- *What are the placements for CSE at IIIT Allahabad?*\n- *Which is better: CSE at NIT Calicut or ECE at NIT Trichy?*",
    },
  ]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [paramError, setParamError] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedUser = localStorage.getItem("studentUser");
      if (savedUser) {
        setIsLoggedIn(true);
      }
    }
  }, []);
  const bottomRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLInputElement>(null);

  function handleSeoClick(query: string) {
    setInput(query);
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 50);
  }

  function validateParams(): number | null {
    const r = parseInt(rank, 10);
    if (!r || r < 1) {
      setParamError("Enter a valid rank.");
      return null;
    }
    if (!homeState) {
      setParamError("Select your home state.");
      return null;
    }
    if (!branch) {
      setParamError("Select a branch.");
      return null;
    }
    setParamError("");
    return r;
  }

  async function runPredict() {
    const r = validateParams();
    if (!r) return;
    setPredictLoading(true);
    try {
      const data = await predictColleges({
        rank: r,
        category,
        home_state: homeState,
        branch_preferences: branch === "ALL" ? [] : [branch],
        year: cutoffYear,
        exam_type: examType,
        rank_type: rankType,
        round: round,
        student_goals: studentGoals,
        limit: 50,
        max_results: 500,
      });
      setPrediction(data);
      setSidebarFilter("ALL");
      setIsParamBarExpanded(false);
      setActiveMobileTab("colleges");
      
      if (data.session_id) {
        setSessionId(data.session_id);
        setSessionInfo({
          rank: data.rank,
          category: data.seat_category,
          exam_type: data.exam_type || examType,
          round: round,
          total_eligible: data.total_eligible,
        });

        // System session linked silently, trace and sync logs removed from chat view.
      }
    } catch (err) {
      setParamError(err instanceof Error ? err.message : "Could not fetch predictions.");
    } finally {
      setPredictLoading(false);
    }
  }

  function handleCollegeSelect(c: CollegeOption) {
    if (!c) return;
    
    setSelectedCollege(c);
    setSelectedKey(rowId(c));
    setActiveMobileTab("chat");
    
    // Build a contextual prompt - use spaces instead of newlines for input field
    const tierNote = c.tier === "SAFE" ? "(Safe choice)" : c.tier === "TARGET" ? "(Target)" : "(Dream)";
    const prompt = `📍 ${c.college_name} ${tierNote} - ${c.program_name} | Tell me: placements, package, campus culture. Should I pick it?`;
    
    // Update input field with the prompt
    setInput(prompt);
    
    // Focus the chat input box immediately using ref
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 50);
  }

  async function runPreferenceList() {
    const r = validateParams();
    if (!r) return;
    setPrefLoading(true);
    setShowPreferences(true);
    try {
      const data = await generatePreferenceList({
        rank: r,
        category,
        home_state: homeState,
        branch_preferences: branch === "ALL" ? [] : [branch],
        year: cutoffYear,
        exam_type: examType,
        rank_type: rankType,
        round: round,
        student_goals: studentGoals,
        max_choices: 25,
      });
      setPreferenceList(data);
    } catch (err) {
      setParamError(err instanceof Error ? err.message : "Could not generate preference list.");
    } finally {
      setPrefLoading(false);
    }
  }

  async function sendChat(overrideMessage?: string, isLoginBypass?: boolean) {
    const text = (overrideMessage ?? input).trim();
    if (!text || chatLoading) return;
    const r = validateParams();
    if (!r) return;

    const userMessagesCount = messages.filter((m) => m.role === "user").length;
    if (userMessagesCount >= 1 && !isLoggedIn && !isLoginBypass) {
      setPendingMessage(text);
      setShowLoginModal(true);
      return;
    }

    setInput("");
    setIsParamBarExpanded(false);
    const userMsg = text;
    const nextHistory = [...messages, { role: "user" as const, content: userMsg }];
    setMessages(nextHistory);
    setChatLoading(true);

    try {
      const res = await sendChatMessage({
        message: userMsg,
        history: messages.map((m) => ({ role: m.role, content: m.content })),
        rank: r,
        category,
        home_state: homeState,
        branch_preferences: branch === "ALL" ? [] : [branch],
        year: cutoffYear,
        exam_type: examType,
        rank_type: rankType,
        round: round,
        student_goals: studentGoals,
        focused_college: selectedCollege?.college_name,
        session_id: sessionId || undefined,
        selected_card: selectedCollege ? {
          college: selectedCollege.college_name,
          branch: selectedCollege.branch,
          program_name: selectedCollege.program_name,
          closing_rank: selectedCollege.closing_rank,
          classification: selectedCollege.tier,
          category: category,
          round: round
        } : undefined,
        sidebar_colleges: prediction
          ? (prediction.all && prediction.all.length > 0
              ? prediction.all
              : [...prediction.safe, ...prediction.target, ...prediction.dream]
            )
              .slice(0, 10)
              .map((c) => ({
                college_name: c.college_name,
                branch: c.branch,
                closing_rank: c.closing_rank,
                tier: c.tier,
              }))
          : undefined,
      });
      setMessages([...nextHistory, { role: "model", content: res.reply, verified_cards: res.verified_cards }]);
      console.log("Counselling Copilot Context Used:", res.context_used);
      if (res.preference_list) {

        setPreferenceList(res.preference_list);
        setShowPreferences(true);
      }

      // Automatically sync/update sessionId and sessionInfo if returned or updated on backend
      if (res.context_used && res.context_used.session_info) {
        const s = res.context_used.session_info;
        if (s.session_id) {
          setSessionId(s.session_id);
          setSessionInfo({
            rank: s.rank ?? r,
            category: s.category ?? category,
            exam_type: s.exam_type ?? examType,
            round: s.round ?? round,
            total_eligible: s.total_eligible,
          });
        }
      }
    } catch {
      setMessages([
        ...nextHistory,
        {
          role: "model",
          content: "Could not reach the API. Start Django with `python manage.py runserver`.",
        },
      ]);
    } finally {
      setChatLoading(false);
      if (!overrideMessage) {
        setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 80);
      }
    }
  }

  return (
    <div className="flex h-screen flex-col bg-[#060609] text-slate-100 overflow-hidden bg-[linear-gradient(to_right,#1f293708_1px,transparent_1px),linear-gradient(to_bottom,#1f293708_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] relative">
      {/* Integrated top header with scrollable SEO template chips */}
      <header className="border-b border-slate-800 bg-slate-950/70 backdrop-blur shrink-0 h-14 z-50 flex items-center justify-between px-4 w-full">
        <div className="flex items-center gap-3 shrink-0">
          <div>
            <h1 className="text-sm font-extrabold text-brand-400 tracking-tight leading-tight">
              JoSAA RankPilot AI
            </h1>
            <p className="text-[9px] text-slate-400 font-medium">
              AI JEE Main College Predictor & Choice Filling
            </p>
          </div>
          <button
            onClick={() => setTourStep(0)}
            className="ml-3 bg-brand-950/40 hover:bg-brand-900/60 text-[10px] text-brand-400 border border-brand-500/30 rounded-full px-2.5 py-1.5 transition-all cursor-pointer font-bold flex items-center gap-1 active:scale-95 shrink-0"
            title="Start Onboarding Tour"
          >
            <span>💡 Tour</span>
          </button>
        </div>

        {/* Scrollable SEO examples side-by-side */}
        <div id="tour-queries" className="flex-1 overflow-x-auto scrollbar-none flex items-center gap-1.5 px-4 justify-end">
          <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider whitespace-nowrap mr-1 hidden sm:inline">
            Repeated Queries:
          </span>
          {SEO_PAGES.map((page) => (
            <button
              key={page}
              onClick={() => handleSeoClick(page)}
              className="bg-slate-900/60 hover:bg-brand-950/40 text-[10px] text-slate-300 hover:text-brand-400 border border-slate-800 hover:border-brand-500/30 rounded-full px-2.5 py-1 transition-all cursor-pointer whitespace-nowrap active:scale-95 shrink-0"
            >
              {page}
            </button>
          ))}
        </div>
      </header>

      {/* Mobile Tab Switcher */}
      {prediction && (
        <div className="flex lg:hidden shrink-0 bg-slate-950/90 backdrop-blur-md border-b border-slate-900 p-2 gap-2 z-40">
          <button
            onClick={() => setActiveMobileTab("colleges")}
            className={`flex-1 py-2 text-center text-[10.5px] font-black tracking-wider uppercase rounded-xl border transition-all duration-300 ${
              activeMobileTab === "colleges"
                ? "bg-brand-600/10 border-brand-500/40 text-brand-400 shadow-[0_0_12px_rgba(59,130,246,0.1)]"
                : "bg-slate-900/60 border-slate-850 text-slate-500 hover:text-slate-300 hover:bg-slate-900"
            }`}
          >
            📊 Colleges List ({prediction.total_eligible})
          </button>
          <button
            onClick={() => setActiveMobileTab("chat")}
            className={`flex-1 py-2 text-center text-[10.5px] font-black tracking-wider uppercase rounded-xl border transition-all duration-300 ${
              activeMobileTab === "chat"
                ? "bg-brand-600/10 border-brand-500/40 text-brand-400 shadow-[0_0_12px_rgba(59,130,246,0.1)]"
                : "bg-slate-900/60 border-slate-850 text-slate-500 hover:text-slate-300 hover:bg-slate-900"
            }`}
          >
            💬 Riya Mentor Chat
          </button>
        </div>
      )}

      {/* Core layout below header */}
      <div className="flex flex-1 flex-col lg:flex-row min-h-0 overflow-hidden relative">
        {/* Collapsible Left Sidebar */}
        {isSidebarExpanded ? (
          <div
            id="tour-sidebar"
            className={`lg:w-[340px] lg:shrink-0 relative border-r border-slate-900/60 lg:h-full ${
              prediction
                ? (activeMobileTab === "colleges" ? "flex flex-1 h-full w-full" : "hidden lg:flex")
                : "hidden lg:flex lg:h-full lg:w-[280px]"
            }`}
          >
            <CollegeSidebar
              result={prediction}
              loading={predictLoading}
              selectedKey={selectedKey}
              onSelect={handleCollegeSelect}
              filter={sidebarFilter}
              onFilterChange={setSidebarFilter}
            />
            {/* Collapse toggle button */}
            <button
              id="tour-sidebar-toggle-btn"
              onClick={() => setIsSidebarExpanded(false)}
              className="absolute top-3.5 right-3 z-50 p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
              title="Hide Colleges"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>
        ) : (
          /* Expand toggle handle when sidebar is collapsed */
          <button
            id="tour-sidebar-toggle-btn"
            onClick={() => setIsSidebarExpanded(true)}
            className="absolute top-1/2 -translate-y-1/2 left-0 z-50 p-1 rounded-r-xl border-y border-r border-slate-800 bg-slate-950/90 text-slate-400 hover:text-brand-400 shadow-2xl hover:scale-105 active:scale-95 transition-all cursor-pointer flex flex-col items-center justify-center h-24 w-5 hover:bg-slate-900 group"
            title="Show Colleges"
          >
            <svg className="h-4 w-4.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            <span className="text-[7.5px] font-extrabold uppercase tracking-widest text-slate-500 group-hover:text-brand-400 [writing-mode:vertical-lr] rotate-180 mt-1.5">Colleges</span>
          </button>
        )}

        {/* Main chat column */}
        <div
          className={`flex min-h-0 flex-1 flex-col bg-[#08080d] border-l border-slate-905 relative bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.06),rgba(255,255,255,0))] ${
            prediction && activeMobileTab !== "chat" ? "hidden lg:flex" : "flex"
          }`}
        >
          {/* Collapsible Parameter bar */}
          <div id="tour-params" className="shrink-0 border-b border-slate-800 bg-gradient-to-r from-slate-950 to-[#0e0e16] px-4 py-3 transition-all duration-300">
            {isParamBarExpanded ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Counselling Parameters</span>
                  <button
                    onClick={() => setIsParamBarExpanded(false)}
                    className="flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 font-semibold transition bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-lg cursor-pointer"
                  >
                    <span>Hide Panel</span>
                    <svg className="h-3.5 w-3.5 transform rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:flex lg:flex-wrap items-end gap-3 w-full">
                  <label className="flex flex-col gap-1 w-full lg:w-auto lg:min-w-[130px]">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">Exam Type</span>
                    <select
                      value={examType}
                      onChange={(e) => setExamType(e.target.value as ExamType)}
                      className="rounded-xl border border-slate-800/80 px-3 py-2 text-xs font-bold text-brand-400 bg-slate-900/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 cursor-pointer w-full hover:bg-slate-900 hover:border-slate-700 transition"
                    >
                      {EXAM_TYPES.map((e) => (
                        <option key={e.value} value={e.value} className="bg-slate-950 text-slate-100">
                          {e.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 w-full lg:w-auto lg:min-w-[130px]">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">Rank Type</span>
                    <select
                      value={rankType}
                      onChange={(e) => setRankType(e.target.value as RankType)}
                      className="rounded-xl border border-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 bg-slate-900/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 cursor-pointer w-full hover:bg-slate-900 hover:border-slate-700 transition"
                    >
                      {RANK_TYPES.map((r) => (
                        <option key={r.value} value={r.value} className="bg-slate-950 text-slate-100">
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 w-full lg:w-auto">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">
                      {rankType === "CRL" ? "CRL Rank" : `${category} Rank`}
                    </span>
                    <input
                      type="number"
                      value={rank}
                      onChange={(e) => setRank(e.target.value)}
                      placeholder={examType === "JEE_ADVANCED" ? "5000" : "20000"}
                      className="rounded-xl border border-slate-800 bg-slate-950 text-slate-100 px-3 py-2 text-xs font-extrabold focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 w-full hover:border-slate-750 transition"
                    />
                  </label>

                  <label className="flex flex-col gap-1 w-full lg:w-auto">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">Category</span>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="rounded-xl border border-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 bg-slate-900/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 cursor-pointer w-full hover:bg-slate-900 hover:border-slate-700 transition"
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c} value={c} className="bg-slate-950 text-slate-100">
                          {c}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 w-full lg:w-auto lg:min-w-[110px]">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">Round</span>
                    <select
                      value={round}
                      onChange={(e) => setRound(e.target.value)}
                      className="rounded-xl border border-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 bg-slate-900/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 cursor-pointer w-full hover:bg-slate-900 hover:border-slate-700 transition"
                    >
                      {ROUND_OPTIONS.map((r) => (
                        <option key={r.value} value={r.value} className="bg-slate-950 text-slate-100">
                          {r.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 w-full lg:w-auto lg:min-w-[140px] lg:flex-1">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">Home state</span>
                    <select
                      value={homeState}
                      onChange={(e) => setHomeState(e.target.value)}
                      className="rounded-xl border border-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 bg-slate-900/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 cursor-pointer w-full hover:bg-slate-900 hover:border-slate-700 transition"
                    >
                      {INDIAN_STATES.map((s) => (
                        <option key={s} value={s} className="bg-slate-950 text-slate-100">
                          {s}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 w-full lg:w-auto lg:min-w-[120px]">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">Branch</span>
                    <select
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      className="rounded-xl border border-slate-800/80 px-3 py-2 text-xs font-bold text-slate-300 bg-slate-900/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 cursor-pointer w-full hover:bg-slate-900 hover:border-slate-700 transition"
                    >
                      {BRANCH_OPTIONS.map((b) => (
                        <option key={b.value} value={b.value} className="bg-slate-950 text-slate-100">
                          {b.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 w-full lg:w-auto lg:min-w-[90px]">
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-slate-500">Year</span>
                    <select
                      value={cutoffYear}
                      onChange={(e) => setCutoffYear(Number(e.target.value))}
                      className="rounded-xl border border-slate-800/80 px-3 py-2 text-xs font-bold text-brand-400 bg-slate-900/60 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10 cursor-pointer w-full hover:bg-slate-900 hover:border-slate-700 transition"
                    >
                      {CUTOFF_YEARS.map((y) => (
                        <option key={y.value} value={y.value} className="bg-slate-950 text-slate-100">
                          {y.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="flex gap-2 w-full lg:w-auto shrink-0 select-none">
                    <button
                      type="button"
                      onClick={runPredict}
                      disabled={predictLoading}
                      className="flex-1 lg:flex-none rounded-xl bg-gradient-to-r from-brand-600 to-blue-700 hover:from-brand-500 hover:to-blue-600 text-white font-extrabold text-xs px-5 py-3.5 shadow-lg shadow-brand-500/10 transition hover:scale-[1.02] active:scale-[0.98] cursor-pointer disabled:opacity-50"
                    >
                      {predictLoading ? "Predicting…" : "Predict"}
                    </button>
                    <button
                      type="button"
                      onClick={runPreferenceList}
                      disabled={prefLoading || predictLoading}
                      className="flex-1 lg:flex-none rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-brand-500/35 text-brand-400 font-extrabold text-xs px-4 py-3.5 transition hover:scale-[1.02] active:scale-[0.98] cursor-pointer disabled:opacity-50"
                    >
                      {prefLoading ? "…" : "📋 Preference List"}
                    </button>
                  </div>
                  {isLoggedIn && (
                    <button
                      type="button"
                      onClick={() => {
                        if (typeof window !== "undefined") {
                          localStorage.removeItem("studentUser");
                        }
                        setIsLoggedIn(false);
                      }}
                      className="rounded-lg border border-red-800/80 px-3 py-2 text-sm font-semibold text-red-400 hover:bg-red-950/30 active:scale-[0.98] transition-all"
                    >
                      Logout
                    </button>
                  )}
                </div>
                <label className="flex flex-col gap-0.5 w-full">
                  <span className="text-[10px] font-semibold uppercase text-slate-400">
                    Your priorities (AI remembers)
                  </span>
                  <input
                    value={studentGoals}
                    onChange={(e) => setStudentGoals(e.target.value)}
                    placeholder="e.g. prioritize placements & coding culture, avoid core branches"
                    className="w-full rounded-lg border border-slate-800 bg-slate-950 text-slate-100 px-2 py-1.5 text-xs focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  />
                </label>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 min-h-8 py-1.5 w-full">
                <div 
                  className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-slate-300 cursor-pointer select-none"
                  onClick={() => setIsParamBarExpanded(true)}
                >
                  <span className="bg-brand-950/40 text-brand-400 px-1.5 py-0.5 rounded font-bold border border-brand-900/30 uppercase text-[9px] tracking-wide">
                    {examType === "JEE_ADVANCED" ? "JEE Advanced" : "JEE Main"}
                  </span>
                  <span className="font-semibold text-slate-100">Rank: <span className="text-brand-400">{rank || "—"}</span></span>
                  <span className="text-slate-600">•</span>
                  <span>Category: <span className="font-medium text-slate-200">{category}</span></span>
                  <span className="text-slate-600">•</span>
                  <span>State: <span className="font-medium text-slate-200">{homeState}</span></span>
                  <span className="text-slate-600">•</span>
                  <span>Branch: <span className="font-medium text-slate-200">{branch === "ALL" ? "All" : branch}</span></span>
                  <span className="text-slate-600">•</span>
                  <span>Year: <span className="font-medium text-slate-200">{cutoffYear}</span></span>
                </div>
                <button
                  onClick={() => setIsParamBarExpanded(true)}
                  className="flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 font-semibold transition bg-slate-900 border border-slate-800 px-2.5 py-1.5 rounded-xl cursor-pointer self-start sm:self-auto"
                >
                  <span>Edit Params</span>
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            )}
            {paramError && (
              <p className="mt-2 text-xs text-red-400">{paramError}</p>
            )}
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-4 relative">

            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} items-start gap-3 w-full`}
              >
                {m.role === "model" && (
                  <div className="flex h-8.5 w-8.5 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 text-white font-extrabold text-xs shadow-[0_0_12px_rgba(99,102,241,0.25)] border border-brand-500/20 select-none">
                    R
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3.5 ${
                    m.role === "user"
                      ? "bg-gradient-to-br from-brand-600 to-blue-700 text-white text-sm shadow-lg shadow-brand-900/10 border border-brand-550/20 rounded-tr-none"
                      : "bg-slate-900/50 backdrop-blur-sm border border-slate-855 text-slate-200 shadow-md rounded-tl-none"
                  }`}
                >
                  {m.role === "user" ? (
                    <div>
                      <div className="flex items-center justify-end gap-1.5 mb-1.5 opacity-80 select-none">
                        <span className="text-[9px] font-black text-brand-200 uppercase tracking-widest">Student</span>
                      </div>
                      <p className="whitespace-pre-wrap text-[13px] leading-relaxed font-sans font-medium">{m.content}</p>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center gap-2 mb-2 select-none border-b border-slate-900/40 pb-1.5">
                        <span className="text-[10px] font-black text-brand-400 uppercase tracking-widest">Riya</span>
                        <span className="text-[8px] bg-brand-950/80 text-brand-400 border border-brand-500/20 px-1.5 py-0.5 rounded font-black tracking-wider uppercase">Mentor</span>
                      </div>
                      <MarkdownMessage content={m.content} />
                      {/* m.verified_cards && m.verified_cards.length > 0 && (
                        <VerifiedReasoningCardsList cards={m.verified_cards} />
                      ) */}
                    </div>
                  )}
                </div>
                {m.role === "user" && (
                  <div className="flex h-8.5 w-8.5 shrink-0 items-center justify-center rounded-xl bg-slate-900/80 text-slate-300 font-extrabold text-xs border border-slate-800 shadow-sm select-none">
                    S
                  </div>
                )}
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <RAGStatusIndicator />
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {showPreferences && (
            <Suspense fallback={<div className="border-t border-slate-800 p-3 bg-slate-950 h-32 animate-pulse" />}>
              <PreferencePanel
                data={preferenceList}
                loading={prefLoading}
                onClose={() => setShowPreferences(false)}
              />
            </Suspense>
          )}

          {showLoginModal && (
            <LoginModal
              onSuccess={(student) => {
                setIsLoggedIn(true);
                setShowLoginModal(false);
                if (pendingMessage) {
                  sendChat(pendingMessage, true);
                  setPendingMessage(null);
                }
              }}
              onClose={() => {
                setShowLoginModal(false);
                setPendingMessage(null);
              }}
            />
          )}

          {/* Input */}
          <div id="tour-chat-input" className="shrink-0 border-t border-slate-850 p-4 bg-[#08080c]">
            <div className="relative flex items-center bg-slate-950 rounded-2xl border border-slate-800 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/10 transition-all duration-300 w-full shadow-lg">
              <input
                ref={chatInputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendChat())
                }
                placeholder={
                  selectedCollege
                    ? `Ask about ${selectedCollege.college_name}…`
                    : "Ask about placements, campus life, preference strategy…"
                }
                className="flex-1 bg-transparent text-slate-200 pl-4 pr-12 py-3.5 text-sm focus:outline-none placeholder:text-slate-500"
              />
              <button
                type="button"
                onClick={() => sendChat()}
                disabled={chatLoading || !input.trim()}
                className="absolute right-2 p-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-30 disabled:bg-transparent disabled:text-slate-650 text-white transition active:scale-95 cursor-pointer flex items-center justify-center shadow-md"
                title="Send Message"
              >
                <svg className="h-4 w-4 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {tourStep >= 0 && (
        <TourOverlay
          stepIndex={tourStep}
          totalSteps={TOUR_STEPS.length}
          onClose={() => {
            setTourStep(-1);
            if (typeof window !== "undefined") {
              localStorage.setItem("hasSeenTour_v3", "true");
            }
          }}
          onNext={() => {
            if (tourStep < TOUR_STEPS.length - 1) {
              setTourStep(tourStep + 1);
            } else {
              setTourStep(-1);
              if (typeof window !== "undefined") {
                localStorage.setItem("hasSeenTour_v3", "true");
              }
            }
          }}
          onBack={() => {
            if (tourStep > 0) {
              setTourStep(tourStep - 1);
            }
          }}
        />
      )}
    </div>
  );
}

// ----------------------------------------------------
// USER ONBOARDING TOUR DATA & DYNAMIC OVERLAY
// ----------------------------------------------------

interface TourStep {
  title: string;
  content: string;
  targetId: string;
  placement: "bottom" | "right" | "left" | "top" | "center";
}

const TOUR_STEPS: TourStep[] = [
  {
    title: "Welcome to JoSAA RankPilot AI! 🚀",
    content: "Let's take a quick 1-minute guided tour to show you how to find and query your dream colleges.",
    targetId: "",
    placement: "center",
  },
  {
    targetId: "tour-params",
    title: "1. Counselling Parameters",
    content: "Configure your Rank, Category, State, and Branch. This panel collapses automatically to save vertical space when chat starts, but you can expand/edit it anytime by clicking 'Edit Params'.",
    placement: "bottom",
  },
  {
    targetId: "tour-sidebar",
    title: "2. Eligible Colleges",
    content: "Your eligible colleges appear here from the verified database. Use filters to look for safe, target, or dream options.",
    placement: "right",
  },
  {
    targetId: "tour-college-list",
    title: "3. Auto-Query Colleges",
    content: "Clicking any college card in the sidebar automatically populates a smart query in the chat box (like the sample loaded below) to ask about placements and campus life!",
    placement: "right",
  },
  {
    targetId: "tour-sidebar-toggle-btn",
    title: "4. Full Screen Width Toggle",
    content: "Click this arrow button to collapse the sidebar so the AI chat can occupy the full screen width. You can easily slide it back by hovering & clicking the floating tab on the left edge.",
    placement: "right",
  },
  {
    targetId: "tour-queries",
    title: "5. Repeated / Quick Queries",
    content: "Tap any popular question here to instantly load that query into the chat input box (like the sample loaded below). Convenient for quick comparisons!",
    placement: "bottom",
  },
  {
    targetId: "tour-chat-input",
    title: "6. Smart AI Chat",
    content: "Ask Riya any custom questions about college placements, coding culture, or counseling choices. Conversations are scrollable, and technical info is replaced by a friendly thinking status bar.",
    placement: "top",
  }
];

interface TourOverlayProps {
  stepIndex: number;
  totalSteps: number;
  onClose: () => void;
  onNext: () => void;
  onBack: () => void;
}

function TourOverlay({ stepIndex, totalSteps, onClose, onNext, onBack }: TourOverlayProps) {
  const step = TOUR_STEPS[stepIndex];
  const [coords, setCoords] = useState<{ top: number; left: number; width: number; height: number } | null>(null);

  useEffect(() => {
    if (!step || !step.targetId) {
      setCoords(null);
      return;
    }
    const updatePosition = () => {
      const el = document.getElementById(step.targetId);
      if (el) {
        const rect = el.getBoundingClientRect();
        setCoords({
          top: rect.top + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width,
          height: rect.height,
        });
      } else {
        setCoords(null);
      }
    };
    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition);
    };
  }, [stepIndex, step?.targetId]);

  if (!step) return null;

  let tooltipStyle: React.CSSProperties = {
    position: "fixed",
    zIndex: 9999,
  };

  if (!coords) {
    tooltipStyle = {
      ...tooltipStyle,
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      width: "360px",
    };
  } else {
    const space = 14;
    const tooltipWidth = 320;

    if (step.placement === "bottom") {
      tooltipStyle = {
        ...tooltipStyle,
        top: `${coords.top + coords.height + space}px`,
        left: `${coords.left + coords.width / 2}px`,
        transform: "translateX(-50%)",
        width: `${tooltipWidth}px`,
      };
    } else if (step.placement === "right") {
      tooltipStyle = {
        ...tooltipStyle,
        top: `${coords.top + coords.height / 2}px`,
        left: `${coords.left + coords.width + space}px`,
        transform: "translateY(-50%)",
        width: `${tooltipWidth}px`,
      };
    } else if (step.placement === "left") {
      tooltipStyle = {
        ...tooltipStyle,
        top: `${coords.top + coords.height / 2}px`,
        left: `${coords.left - tooltipWidth - space}px`,
        transform: "translateY(-50%)",
        width: `${tooltipWidth}px`,
      };
    } else if (step.placement === "top") {
      tooltipStyle = {
        ...tooltipStyle,
        top: `${coords.top - 180 - space}px`, // safe height approximation
        left: `${coords.left + coords.width / 2}px`,
        transform: "translateX(-50%)",
        width: `${tooltipWidth}px`,
      };
    }
  }

  const clipPathStr = coords
    ? `polygon(
        0% 0%, 0% 100%,
        ${coords.left - 4}px 100%,
        ${coords.left - 4}px ${coords.top - 4}px,
        ${coords.left + coords.width + 4}px ${coords.top - 4}px,
        ${coords.left + coords.width + 4}px ${coords.top + coords.height + 4}px,
        ${coords.left - 4}px ${coords.top + coords.height + 4}px,
        ${coords.left - 4}px 100%,
        100% 100%, 100% 0%
      )`
    : "none";

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-950/75 backdrop-blur-[2px] z-[9990] transition-all duration-300 pointer-events-auto" 
        style={{ clipPath: clipPathStr }}
        onClick={onClose} 
      />

      {coords && (
        <div
          className="absolute z-[9995] rounded-xl ring-4 ring-brand-500 ring-offset-4 ring-offset-slate-950 pointer-events-none shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all duration-300"
          style={{
            top: `${coords.top}px`,
            left: `${coords.left}px`,
            width: `${coords.width}px`,
            height: `${coords.height}px`,
          }}
        />
      )}

      <div
        style={tooltipStyle}
        className="bg-slate-950 border border-slate-800 text-slate-100 p-5 rounded-2xl shadow-2xl backdrop-blur-md ring-1 ring-white/10 pointer-events-auto flex flex-col gap-3.5 max-w-[90vw]"
      >
        <div className="flex items-start justify-between">
          <h3 className="text-xs font-extrabold text-brand-400 uppercase tracking-widest">
            {step.title}
          </h3>
          <span className="text-[10px] text-slate-500 font-bold font-mono">
            {stepIndex + 1} / {totalSteps}
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-medium">
          {step.content}
        </p>
        <div className="flex items-center justify-between mt-1 pt-3 border-t border-slate-900">
          <button
            onClick={onClose}
            className="text-[11px] font-bold text-slate-500 hover:text-slate-300 transition px-1.5 py-1 rounded cursor-pointer"
          >
            Skip
          </button>
          <div className="flex items-center gap-2">
            {stepIndex > 0 && (
              <button
                onClick={onBack}
                className="bg-slate-900 hover:bg-slate-800 text-[11px] font-bold text-slate-300 border border-slate-800 px-3 py-1.5 rounded-lg transition active:scale-95 cursor-pointer"
              >
                Back
              </button>
            )}
            <button
              onClick={onNext}
              className="bg-brand-600 hover:bg-brand-500 text-[11px] font-bold text-white shadow-md px-3.5 py-1.5 rounded-lg transition active:scale-95 cursor-pointer"
            >
              {stepIndex === totalSteps - 1 ? "Finish" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

interface LoginModalProps {
  onSuccess: (data: any) => void;
  onClose: () => void;
}

function LoginModal({ onSuccess, onClose }: LoginModalProps) {
  const [name, setName] = useState("");
  const [gender, setGender] = useState("Male");
  const [mobile, setMobile] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter your name");
      return;
    }
    if (!/^\d{10}$/.test(mobile)) {
      setError("Please enter a valid 10-digit mobile number");
      return;
    }
    setError("");
    setLoading(true);

    try {
      const student = await registerStudent({
        name: name.trim(),
        gender,
        mobile_number: mobile,
      });

      setLoading(false);
      if (typeof window !== "undefined") {
        localStorage.setItem("studentUser", JSON.stringify(student));
      }
      onSuccess(student);
    } catch (err: any) {
      setLoading(false);
      setError("Failed to register. Please try again.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity duration-300"
        onClick={onClose}
      />

      <div className="relative w-full max-w-md transform overflow-hidden rounded-2xl bg-slate-950 p-6 shadow-2xl transition-all duration-300 border border-slate-800 animate-in fade-in zoom-in-95 duration-200">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-1 text-slate-500 hover:bg-slate-900 hover:text-slate-300 transition"
          aria-label="Close modal"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="text-center pb-2">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-950/40 text-brand-400 border border-brand-900/40 mb-3">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-slate-100">Unlock AI Counsellor</h3>
            <p className="text-xs text-slate-400 mt-1">
              Enter your details to continue your personalized chat guidance session.
            </p>
          </div>

          {error && (
            <div className="rounded-lg bg-red-950/40 p-2.5 text-xs text-red-400 border border-red-900/30">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">
                Full Name
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Prasanth Kumar"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-900/60 text-slate-100 px-3.5 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">
                Gender
              </label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-900/60 text-slate-100 px-3.5 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              >
                <option value="Male" className="bg-slate-950 text-slate-100">Male</option>
                <option value="Female" className="bg-slate-950 text-slate-100">Female</option>
                <option value="Other" className="bg-slate-950 text-slate-100">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">
                Mobile Number
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm text-slate-500 font-medium">
                  +91
                </span>
                <input
                  type="tel"
                  required
                  maxLength={10}
                  placeholder="98765 43210"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value.replace(/\D/g, ""))}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900/60 text-slate-100 pl-12 pr-3.5 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-brand-600 py-3 text-sm font-semibold text-white shadow-md hover:bg-brand-500 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-1.5"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Logging in…
              </>
            ) : (
              "Verify & Continue"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

function RAGStatusIndicator() {
  const steps = [
    { label: "Analyzing your rank and goals..." },
    { label: "Searching JoSAA database..." },
    { label: "Comparing college options..." },
    { label: "Writing custom advice..." },
  ];

  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 1800);

    return () => clearInterval(interval);
  }, []);

  const progressPercent = Math.round(((currentStep + 0.5) / steps.length) * 100);

  return (
    <div className="flex flex-col gap-3 p-4 w-80 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur shadow-lg transition-all duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-brand-400 animate-ping" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-brand-400">
            Thinking...
          </span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono font-bold">
          {progressPercent}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-900">
        <div 
          className="h-full bg-gradient-to-r from-brand-500 to-emerald-400 rounded-full transition-all duration-500 shadow-[0_0_8px_rgba(34,197,94,0.4)] animate-pulse"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className="space-y-1.5 mt-1">
        {steps.map((step, idx) => {
          const isCompleted = idx < currentStep;
          const isActive = idx === currentStep;
          return (
            <div
              key={idx}
              className={`flex items-center gap-2 text-xs transition-all duration-300 ${
                isActive 
                  ? "text-slate-100 font-medium opacity-100 scale-100" 
                  : isCompleted 
                    ? "text-emerald-400 opacity-60 scale-95" 
                    : "text-slate-600 opacity-30 scale-95"
              }`}
            >
              <span className="flex items-center justify-center w-4.5 h-4.5 shrink-0 font-bold text-center">
                {isCompleted ? "✓" : "•"}
              </span>
              <span className="truncate">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
