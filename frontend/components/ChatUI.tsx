"use client";

import { useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api";
import { MarkdownMessage } from "./MarkdownMessage";
import { CollegeList } from "./CollegeList";

type Message = {
  role: "user" | "model";
  content: string;
  predictions?: {
    dream: Parameters<typeof CollegeList>[0]["items"];
    target: Parameters<typeof CollegeList>[0]["items"];
    safe: Parameters<typeof CollegeList>[0]["items"];
    unlikely?: Parameters<typeof CollegeList>[0]["items"];
  } | null;
};

export function ChatUI() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "model",
      content:
        "Hi! I'm your JoSAA counselling copilot. Tell me your rank, category, and state — for example: *I got 20k OBC rank from Andhra Pradesh, suggest best CSE colleges*.",
    },
  ]);
  const [input, setInput] = useState("");
  const [rank, setRank] = useState("");
  const [category, setCategory] = useState("OBC");
  const [homeState, setHomeState] = useState("");
  const [loading, setLoading] = useState(false);
  const [geminiHint, setGeminiHint] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function send() {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    const nextHistory = [...messages, { role: "user" as const, content: userMsg }];
    setMessages(nextHistory);
    setLoading(true);
    setGeminiHint(null);
    try {
      const res = await sendChatMessage({
        message: userMsg,
        history: messages.map((m) => ({ role: m.role, content: m.content })),
        rank: rank ? parseInt(rank, 10) : undefined,
        category: category || undefined,
        home_state: homeState || undefined,
      });
      if (!res.context_used.gemini_enabled) {
        setGeminiHint(
          "Gemini not active — add GEMINI_API_KEY to `.env` at project root and restart Django."
        );
      }
      const preds = res.predictions;
      setMessages([
        ...nextHistory,
        {
          role: "model",
          content: res.reply,
          predictions: preds
            ? {
                dream: preds.dream || [],
                target: preds.target || [],
                safe: preds.safe || [],
                unlikely: preds.unlikely || [],
              }
            : null,
        },
      ]);
    } catch {
      setMessages([
        ...nextHistory,
        {
          role: "model",
          content:
            "Could not reach the API. Start Django: `cd backend/django-app && python manage.py runserver`",
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }

  return (
    <div className="flex h-[calc(100vh-12rem)] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg">
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3 text-sm">
        <input
          type="number"
          placeholder="Rank"
          value={rank}
          onChange={(e) => setRank(e.target.value)}
          className="w-28 rounded-lg border border-slate-200 bg-white px-3 py-1.5"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5"
        >
          {["GENERAL", "OBC", "SC", "ST", "EWS"].map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Home state (optional)"
          value={homeState}
          onChange={(e) => setHomeState(e.target.value)}
          className="min-w-[140px] flex-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5"
        />
      </div>

      {geminiHint && (
        <p className="bg-amber-50 px-4 py-2 text-xs text-amber-800 border-b border-amber-100">
          {geminiHint}
        </p>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[92%] rounded-2xl px-4 py-3 ${
                m.role === "user"
                  ? "bg-brand-600 text-white"
                  : "bg-slate-50 text-slate-800 border border-slate-100"
              }`}
            >
              {m.role === "user" ? (
                <p className="text-sm whitespace-pre-wrap">{m.content}</p>
              ) : (
                <>
                  <MarkdownMessage content={m.content} />
                  {m.predictions && (
                    <div className="mt-4 space-y-4 border-t border-slate-200 pt-4">
                      <CollegeList title="Dream" items={m.predictions.dream} />
                      <CollegeList title="Target" items={m.predictions.target} />
                      <CollegeList title="Safe" items={m.predictions.safe} />
                      {m.predictions.unlikely && m.predictions.unlikely.length > 0 && (
                        <CollegeList title="Unlikely — unrealistic" items={m.predictions.unlikely} />
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-1 px-2">
            <span className="h-2 w-2 animate-bounce rounded-full bg-brand-400" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-brand-400 [animation-delay:0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-brand-400 [animation-delay:0.3s]" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-slate-100 bg-white p-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
          placeholder="Ask about colleges, CSE options, preference strategy…"
          className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
        />
        <button
          type="button"
          onClick={send}
          disabled={loading}
          className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
