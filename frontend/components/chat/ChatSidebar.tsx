import React from "react";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { Conversation } from "@/services/chat";
import { UserResponse } from "@/services/auth";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onCreateNew: () => void;
  error?: boolean;
  onRetry?: () => void;
  user: UserResponse | null;
  onLogout: () => void;
  onLanguageChange: (lang: string) => void;
  onOpenCompanyInfo: () => void;
  onOpenContact: () => void;
}

export default function ChatSidebar({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onCreateNew,
  error,
  onRetry,
  user,
  onLogout,
  onLanguageChange,
  onOpenCompanyInfo,
  onOpenContact
}: ChatSidebarProps) {
  return (
    <div className="w-80 border-r border-slate-800 bg-slate-900/50 flex flex-col backdrop-blur-md">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-800/80">
        <button
          onClick={onCreateNew}
          aria-label="Start new conversation"
          className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 transition-all duration-300 transform active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
        >
          <Plus size={18} />
          <span>New Chat</span>
        </button>
      </div>

      {error && (
        <div className="mx-4 my-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex flex-col items-center gap-1.5 backdrop-blur-md">
          <span className="font-medium text-center">Failed to load chat history.</span>
          <button 
            onClick={onRetry}
            aria-label="Retry loading chat history"
            className="w-full py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 transition-colors font-semibold focus-visible:ring-2 focus-visible:ring-amber-500 focus:outline-none"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-800">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-sm">
            No previous conversations.
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv._id === activeId;
            return (
              <div
                key={conv._id}
                onClick={() => onSelect(conv._id)}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all duration-300 focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none ${
                  isActive
                    ? "bg-slate-800/60 border border-slate-700/50 text-white"
                    : "hover:bg-slate-800/30 text-slate-400 hover:text-slate-200"
                }`}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelect(conv._id);
                  }
                }}
              >
                <div className="flex items-center gap-3 overflow-hidden mr-2">
                  <MessageSquare
                    size={16}
                    className={`flex-shrink-0 ${
                      isActive ? "text-violet-400" : "text-slate-500"
                    }`}
                  />
                  <span className="truncate text-sm font-medium leading-none">
                    {conv.title}
                  </span>
                </div>

                {/* Delete button (only visible on hover or if active) */}
                <button
                  onClick={(e) => onDelete(conv._id, e)}
                  aria-label={`Delete conversation ${conv.title}`}
                  className={`opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all duration-300 focus-visible:ring-2 focus-visible:ring-red-500 focus:outline-none ${
                    isActive ? "opacity-100" : ""
                  }`}
                  title="Delete Conversation"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Sidebar Footer with Profile & Controls */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 space-y-3">
        {/* User Info */}
        {user && (
          <div className="flex items-center gap-3 px-1.5 py-1">
            <div className="w-9 h-9 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400 font-bold text-sm">
              {user.full_name ? user.full_name.split(" ").map(n => n[0]).join("").toUpperCase() : "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-200 truncate leading-tight">
                {user.full_name}
              </p>
              <p className="text-xs text-slate-500 truncate leading-none mt-0.5">
                {user.role.toUpperCase()}
              </p>
            </div>
          </div>
        )}

        {/* Dropdown controls & Actions */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <button
            onClick={() => onOpenCompanyInfo?.()}
            aria-label="About Nexora Technologies"
            className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/60 border border-slate-800 text-slate-400 hover:text-slate-200 transition-all duration-300 focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
            title="About Nexora"
          >
            <span>About</span>
          </button>
          <button
            onClick={() => onOpenContact?.()}
            aria-label="Contact Customer Support"
            className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/60 border border-slate-800 text-slate-400 hover:text-slate-200 transition-all duration-300 focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
            title="Contact Support"
          >
            <span>Contact</span>
          </button>
        </div>

        {/* Language & Logout row */}
        <div className="flex items-center justify-between gap-2 pt-1">
          <select
            value={user?.preferred_language || "en"}
            onChange={(e) => onLanguageChange?.(e.target.value)}
            aria-label="Select preferred language"
            className="bg-slate-800 border border-slate-800 rounded-lg text-slate-400 text-xs px-2.5 py-1.5 focus:outline-none focus:border-slate-700/50 cursor-pointer hover:bg-slate-800/80 transition-colors focus-visible:ring-2 focus-visible:ring-violet-500"
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="mr">मराठी</option>
          </select>
          
          <button
            onClick={onLogout}
            aria-label="Logout session"
            className="flex items-center gap-1 py-1.5 px-3 rounded-lg border border-red-500/20 hover:border-red-500/30 bg-red-500/5 hover:bg-red-500/10 text-red-400 hover:text-red-300 transition-all duration-300 text-xs font-medium focus-visible:ring-2 focus-visible:ring-red-500 focus:outline-none"
          >
            <span>Logout</span>
          </button>
        </div>
      </div>
    </div>
  );
}
