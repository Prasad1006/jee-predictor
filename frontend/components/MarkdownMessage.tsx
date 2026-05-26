"use client";

import type { ReactNode } from "react";

/** Lightweight markdown-ish rendering without extra deps */
export function MarkdownMessage({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-2 ml-4 list-disc space-y-1">
          {listItems.map((item, i) => (
            <li key={i} dangerouslySetInnerHTML={{ __html: inlineFormat(item) }} />
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  for (const line of lines) {
    if (line.startsWith("### ")) {
      flushList();
      elements.push(
        <h4
          key={elements.length}
          className="mt-4 mb-2 rounded-xl bg-slate-900/90 border border-slate-800 px-3 py-2 text-sm font-bold text-brand-300 shadow-md shadow-black/20"
        >
          {line.slice(4)}
        </h4>
      );
    } else if (line.startsWith("## ")) {
      flushList();
      elements.push(
        <h3 key={elements.length} className="mt-4 mb-1 text-sm font-extrabold text-slate-100 tracking-wide uppercase">
          {line.slice(3)}
        </h3>
      );
    } else if (line.startsWith("- ") || line.startsWith("✔")) {
      listItems.push(line.startsWith("✔") ? line : line.slice(2));
    } else if (line.trim() === "---") {
      flushList();
      elements.push(<hr key={elements.length} className="my-3 border-slate-800" />);
    } else if (line.trim() === "") {
      flushList();
      elements.push(<br key={elements.length} />);
    } else {
      flushList();
      elements.push(
        <p
          key={elements.length}
          className="my-1.5 text-slate-300 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: inlineFormat(line) }}
        />
      );
    }
  }
  flushList();

  return <div className="prose-sm max-w-none text-sm leading-relaxed">{elements}</div>;
}

function inlineFormat(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(
      /\[(.+?)\]\((.+?)\)/g,
      '<a href="$2" class="text-brand-400 hover:text-brand-300 underline" target="_blank" rel="noreferrer">$1</a>'
    )
    .replace(/`(.+?)`/g, "<code class='bg-slate-950 text-brand-400 border border-slate-850 px-1.5 py-0.5 rounded text-xs font-mono'>$1</code>");
}
