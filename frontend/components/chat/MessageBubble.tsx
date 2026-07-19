import React, { useState } from "react";
import { Copy, Check, FileText, Compass } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Message, Citation } from "@/services/chat";

interface MessageBubbleProps {
  message: Message;
  onSelectSuggestion?: (question: string) => void;
}

export default function MessageBubble({ message, onSelectSuggestion }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  // 1. Parse suggestions if available
  let cleanContent = message.content;
  let suggestions: string[] = [];

  if (message.role === "assistant" && message.content.includes("---SUGGESTIONS---")) {
    const parts = message.content.split("---SUGGESTIONS---");
    cleanContent = parts[0].trim();
    try {
      suggestions = JSON.parse(parts[1].trim());
    } catch (e) {
      console.warn("Failed to parse suggestions JSON payload:", e);
    }
  }

  // 2. Filter citations to only show the ones referenced in cleanContent
  const getUsedCitations = (content: string, citationsList?: Citation[]) => {
    if (!citationsList || citationsList.length === 0) return [];
    // Match pattern like [1], [2], etc.
    const regex = /\[(\d+)\]/g;
    const matches = new Set(Array.from(content.matchAll(regex)).map(m => parseInt(m[1])));
    
    return citationsList
      .map((c, idx) => ({ ...c, originalIdx: idx + 1 }))
      .filter(c => matches.has(c.originalIdx));
  };

  const usedCitations = isUser ? [] : getUsedCitations(cleanContent, message.citations);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(cleanContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error("Failed to copy text:", e);
    }
  };

  return (
    <div className={`flex flex-col mb-4 ${isUser ? "items-end animate-fade-in-right" : "items-start animate-fade-in-left"}`}>
      {/* Main Message Bubble */}
      <div
        className={`max-w-[75%] rounded-2xl p-4 shadow-lg transition-all duration-300 ${
          isUser
            ? "bg-gradient-to-br from-indigo-600 to-violet-600 text-white rounded-br-none"
            : "bg-slate-900/50 border border-slate-800/80 text-slate-100 rounded-bl-none backdrop-blur-md"
        }`}
      >
        {/* Message Content */}
        <div className="prose prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
          {isUser ? (
            cleanContent
          ) : (
            <ReactMarkdown>{cleanContent}</ReactMarkdown>
          )}
        </div>

        {/* Bubble footer with Copy button (only for assistant) */}
        {!isUser && (
          <div className="mt-3 flex items-center justify-between border-t border-slate-800/60 pt-2 text-xs text-slate-400">
            <span className="text-[10px] text-slate-500 font-medium">
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit"
              })}
              {message.is_interrupted && (
                <span className="text-amber-500 ml-2 font-medium">(Interrupted)</span>
              )}
            </span>
            
            <button
              onClick={handleCopy}
              aria-label="Copy response message text"
              className="flex items-center gap-1 hover:text-slate-200 transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none rounded px-1"
              title="Copy response"
            >
              {copied ? (
                <>
                  <Check size={12} className="text-green-400" />
                  <span className="text-green-400 font-semibold">Copied</span>
                </>
              ) : (
                <>
                  <Copy size={12} />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Citations block (only for assistant and if used citations are present) */}
      {!isUser && usedCitations.length > 0 && (
        <div className="mt-2 ml-2 flex flex-wrap gap-2 max-w-[75%]">
          {usedCitations.map((cite, index) => (
            <div
              key={cite.chunk_id || index}
              className="group relative flex items-center gap-1.5 py-1 px-2.5 rounded-lg bg-slate-950/40 border border-slate-800 text-[11px] text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-all duration-300 cursor-help focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
              tabIndex={0}
              aria-label={`Source citation [${cite.originalIdx}]: ${cite.document_title || cite.source_filename}, page ${cite.page_start}`}
            >
              <FileText size={11} className="text-violet-400" />
              <span className="font-semibold text-violet-400">[{cite.originalIdx}]</span>
              <span className="truncate max-w-[120px]">{cite.source_filename}</span>
              <span className="bg-slate-800/80 px-1 rounded text-[9px] text-slate-500 font-medium">
                p.{cite.page_start}
              </span>

              {/* Citations Tooltip / Details Popover */}
              <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block w-64 p-3 rounded-xl bg-slate-950/95 border border-slate-800 text-slate-300 text-xs shadow-2xl backdrop-blur-md z-50 pointer-events-none">
                <div className="font-semibold text-slate-100 truncate mb-1">
                  {cite.document_title || cite.source_filename}
                </div>
                <div className="text-[10px] text-slate-500 mb-2">
                  File: {cite.source_filename} (Pages: {cite.page_start} to {cite.page_end})
                </div>
                <div className="flex justify-between items-center text-[10px] border-t border-slate-800 pt-1.5 text-slate-400">
                  <span className="flex items-center gap-1">
                    <Compass size={10} className="text-indigo-400" />
                    Match: {(cite.similarity_score * 100).toFixed(0)}%
                  </span>
                  <span className="font-mono text-[8px] text-slate-600">
                    ID: {cite.chunk_id?.substring(0, 8)}...
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Suggested Follow-up Questions Section */}
      {!isUser && suggestions.length > 0 && onSelectSuggestion && (
        <div className="mt-2.5 ml-2 flex flex-col gap-1.5 max-w-[75%]">
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider pl-1">
            Suggested Follow-up
          </p>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Suggested follow-up questions">
            {suggestions.map((question, index) => (
              <button
                key={index}
                onClick={() => onSelectSuggestion(question)}
                aria-label={`Ask: ${question}`}
                className="py-1.5 px-3 rounded-xl bg-slate-900/30 hover:bg-violet-600/10 border border-slate-800 hover:border-violet-500/30 text-xs text-slate-400 hover:text-violet-300 transition-all duration-300 text-left font-medium active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
