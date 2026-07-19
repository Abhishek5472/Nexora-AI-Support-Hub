"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Send, 
  Trash2, 
  RotateCcw, 
  Square, 
  MessageSquare,
  AlertCircle,
  ArrowLeft
} from "lucide-react";
import ChatSidebar from "@/components/chat/ChatSidebar";
import MessageBubble from "@/components/chat/MessageBubble";
import { useAuth } from "@/components/auth/AuthProvider";
import { 
  Conversation, 
  Message, 
  Citation,
  createConversation,
  listConversations,
  deleteConversation,
  clearConversationMessages,
  getConversationMessages,
  streamMessage,
  streamRegenerate
} from "@/services/chat";

export default function ChatPage() {
  const { accessToken, user, logout, updateUser } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [streamingCitations, setStreamingCitations] = useState<Citation[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sidebarError, setSidebarError] = useState(false);
  
  // Right-hand drawer panel states
  const [showInfoPanel, setShowInfoPanel] = useState(false);
  const [infoPanelType, setInfoPanelType] = useState<"about" | "contact">("about");
  
  // Polished loading animation phases
  const [loadingPhase, setLoadingPhase] = useState("Searching documentation...");

  // References for abort control and auto-scroll
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // ---------------------------------------------------------------------------
  // Animated Loading Phase Indicator Timer
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (loading && !streamingText) {
      const phases = [
        "Searching documentation...",
        "Reading product guides...",
        "Preparing response...",
        "Generating answer..."
      ];
      let currentIdx = 0;
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoadingPhase(phases[0]);
      const interval = setInterval(() => {
        currentIdx = (currentIdx + 1) % phases.length;
        setLoadingPhase(phases[currentIdx]);
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [loading, streamingText]);

  // ---------------------------------------------------------------------------
  // Data Loaders and State Synchronizers
  // ---------------------------------------------------------------------------
  const fetchConversations = async (retryCount = 0) => {
    try {
      setSidebarError(false);
      const data = await listConversations();
      setConversations(data);
    } catch (e) {
      console.error("Failed to load conversations:", e);
      if (retryCount < 1) {
        console.warn("Retrying fetchConversations due to failure...");
        setTimeout(() => {
          fetchConversations(retryCount + 1);
        }, 1000);
      } else {
        setSidebarError(true);
      }
    }
  };

  const fetchMessages = async (id: string) => {
    try {
      const data = await getConversationMessages(id);
      setMessages(data);
    } catch (e) {
      console.error("Failed to load messages:", e);
    }
  };

  const selectConversation = (id: string | null) => {
    setActiveId(id);
    setStreamingText("");
    setStreamingCitations([]);
    setErrorMsg(null);
  };

  // Load conversations list on load
  useEffect(() => {
    if (accessToken) {
      fetchConversations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  // Fetch messages whenever the active conversation changes
  useEffect(() => {
    if (activeId && accessToken) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchMessages(activeId);
    } else {
      setMessages([]);
    }
  }, [activeId, accessToken]);

  // Auto-scroll on new message or streaming tokens
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  const handleCreateNew = async () => {
    try {
      const newConv = await createConversation();
      setConversations((prev) => [newConv, ...prev]);
      selectConversation(newConv._id);
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      const errDetail = err.response?.data?.detail || "Could not start a new chat.";
      alert(errDetail);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this conversation?")) return;
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c._id !== id));
      if (activeId === id) {
        selectConversation(null);
      }
    } catch (e) {
      console.error("Failed to delete conversation:", e);
    }
  };

  const handleClear = async () => {
    if (!activeId) return;
    if (!confirm("Are you sure you want to clear this conversation's messages?")) return;
    try {
      await clearConversationMessages(activeId);
      setMessages([]);
      setStreamingText("");
      setStreamingCitations([]);
      setErrorMsg(null);
    } catch (e) {
      console.error("Failed to clear messages:", e);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || !activeId || loading) return;
    const text = input.trim();
    setInput("");
    await handleSendQuery(text);
  };

  const handleSendQuery = async (queryText: string) => {
    if (!queryText || !activeId || loading) return;

    setErrorMsg(null);
    setLoading(true);
    setStreamingText("");
    setStreamingCitations([]);

    // Optimistically add user query to local state
    const tempUserMsg: Message = {
      _id: `temp-${Date.now()}`,
      conversation_id: activeId,
      role: "user",
      content: queryText,
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    // Setup abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await streamMessage(
        activeId,
        queryText,
        (token) => {
          setStreamingText((prev) => prev + token);
        },
        (citations) => {
          setStreamingCitations(citations);
        },
        (err) => {
          setErrorMsg(err);
        },
        controller.signal
      );
    } catch (error: unknown) {
      const err = error as Error;
      setErrorMsg(err.message || "Failed to stream message.");
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
      // Refresh messages database log and then clear stream buffer to prevent duplicates
      await fetchMessages(activeId);
      setStreamingText("");
      setStreamingCitations([]);
      fetchConversations();
    }
  };

  const handleRegenerate = async () => {
    if (!activeId || loading) return;

    setErrorMsg(null);
    setLoading(true);
    setStreamingText("");
    setStreamingCitations([]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await streamRegenerate(
        activeId,
        (token) => {
          setStreamingText((prev) => prev + token);
        },
        (citations) => {
          setStreamingCitations(citations);
        },
        (err) => {
          setErrorMsg(err);
        },
        controller.signal
      );
    } catch (error: unknown) {
      const err = error as Error;
      setErrorMsg(err.message || "Failed to regenerate message.");
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
      await fetchMessages(activeId);
      setStreamingText("");
      setStreamingCitations([]);
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleLogout = async () => {
    if (confirm("Are you sure you want to logout?")) {
      await logout();
    }
  };

  const handleLanguageChange = async (lang: string) => {
    try {
      await updateUser({ preferred_language: lang });
    } catch (e) {
      console.error("Failed to update language:", e);
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)] w-full bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* Sidebar Panel Wrapper */}
      <div className={`flex-shrink-0 w-full md:w-80 md:block ${activeId ? "hidden" : "block"}`}>
        <ChatSidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={selectConversation}
          onDelete={handleDelete}
          onCreateNew={handleCreateNew}
          error={sidebarError}
          onRetry={() => fetchConversations(0)}
          user={user}
          onLogout={handleLogout}
          onLanguageChange={handleLanguageChange}
          onOpenCompanyInfo={() => {
            setInfoPanelType("about");
            setShowInfoPanel(true);
          }}
          onOpenContact={() => {
            setInfoPanelType("contact");
            setShowInfoPanel(true);
          }}
        />
      </div>

      {/* Main Workspace */}
      <div className={`flex-1 flex flex-col h-full bg-slate-950/40 relative md:flex ${activeId ? "flex" : "hidden"}`}>
        {activeId ? (
          <>
            {/* Active Header */}
            <div className="p-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/10 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => selectConversation(null)}
                  className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/30 transition-colors focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
                  aria-label="Back to conversations list"
                >
                  <ArrowLeft size={18} />
                </button>
                <MessageSquare className="text-violet-400" size={20} />
                <span className="font-semibold text-slate-200">
                  {conversations.find((c) => c._id === activeId)?.title || "Chat Workspace"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleClear}
                  aria-label="Clear history messages"
                  className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-slate-800 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/30 transition-all duration-300 focus-visible:ring-2 focus-visible:ring-red-500 focus:outline-none"
                  title="Clear conversation messages"
                >
                  <Trash2 size={13} />
                  <span>Clear History</span>
                </button>
              </div>
            </div>

            {/* Message Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-800">
              {messages.map((msg) => (
                <MessageBubble 
                  key={msg._id} 
                  message={msg} 
                  onSelectSuggestion={(question) => handleSendQuery(question)}
                />
              ))}

              {/* Real-time Streaming display */}
              {streamingText && (
                <MessageBubble
                  message={{
                    _id: "streaming",
                    conversation_id: activeId,
                    role: "assistant",
                    content: streamingText,
                    timestamp: new Date().toISOString(),
                    citations: streamingCitations
                  }}
                />
              )}

              {/* Polished animated loading assistant indicator */}
              {loading && !streamingText && (
                <div className="flex items-center gap-3 p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 w-fit max-w-[80%] backdrop-blur-md self-start">
                  <div className="flex space-x-1.5">
                    <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-violet-500 rounded-full animate-bounce"></div>
                  </div>
                  <span className="text-slate-400 text-xs font-semibold animate-pulse tracking-wide uppercase">
                    {loadingPhase}
                  </span>
                </div>
              )}

              {/* Local error banner */}
              {errorMsg && (
                <div className="flex items-center gap-2 p-3.5 rounded-xl border border-red-500/20 bg-red-500/10 text-red-400 text-xs shadow-md">
                  <AlertCircle size={15} />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Form Panel */}
            <div className="p-4 border-t border-slate-800/80 bg-slate-900/10 backdrop-blur-md">
              <form onSubmit={handleSendMessage} className="flex gap-3 max-w-4xl mx-auto items-end">
                <div className="flex-1 relative">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a support question about Nexora products..."
                    rows={1}
                    aria-label="Message text query"
                    className="w-full bg-slate-900 border border-slate-800 rounded-2xl py-3.5 pl-4 pr-12 text-slate-100 text-sm focus:outline-none focus:border-violet-500/50 focus-visible:ring-2 focus-visible:ring-violet-500 resize-none max-h-36 scrollbar-none leading-relaxed"
                  />
                  {loading && (
                    <button
                      type="button"
                      onClick={handleStopGeneration}
                      aria-label="Stop generating response"
                      className="absolute right-3 bottom-3 p-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors focus-visible:ring-2 focus-visible:ring-red-500 focus:outline-none"
                      title="Stop generating response"
                    >
                      <Square size={13} fill="currentColor" />
                    </button>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleRegenerate}
                    disabled={loading || messages.length === 0}
                    aria-label="Regenerate last response"
                    className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed transform active:scale-95 focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
                    title="Regenerate last response"
                  >
                    <RotateCcw size={16} />
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    aria-label="Send message"
                    title="Send message"
                    className="p-3.5 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed transform active:scale-95 focus-visible:ring-2 focus-visible:ring-violet-500 focus:outline-none"
                  >
                    <Send size={16} />
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center max-w-md mx-auto">
            <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-violet-600/20 to-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-6 shadow-xl shadow-indigo-500/5 animate-pulse">
              <MessageSquare size={28} />
            </div>
            <h2 className="text-xl font-bold text-slate-200 mb-2">Nexora AI Support Hub</h2>
            <p className="text-sm text-slate-500 mb-6 leading-relaxed">
              Retrieve authoritative answers grounded in official product guides, warranties, and company documents. Create a new support session to get started.
            </p>
            <button
              onClick={handleCreateNew}
              className="py-3 px-6 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 transition-all duration-300 transform active:scale-95"
            >
              Start New Conversation
            </button>
          </div>
        )}
      </div>

      {/* Sliding Right-Hand Info Panel / Drawer */}
      {showInfoPanel && (
        <div className="w-80 border-l border-slate-800 bg-slate-900/50 flex flex-col backdrop-blur-md relative animate-fade-in-right z-30">
          {/* Header */}
          <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
            <h3 className="font-semibold text-slate-200 text-sm">
              {infoPanelType === "about" ? "About Nexora" : "Contact Support"}
            </h3>
            <button 
              onClick={() => setShowInfoPanel(false)}
              className="text-slate-500 hover:text-slate-300 transition-colors text-xs font-semibold"
            >
              Close
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs text-slate-400 scrollbar-thin scrollbar-thumb-slate-800">
            {infoPanelType === "about" ? (
              <>
                <div className="space-y-1.5">
                  <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">Company Overview</h4>
                  <p className="leading-relaxed">
                    Nexora Technologies is a pioneering hardware, consumer electronics, and SaaS systems developer delivering high-performance tools for modern creative spaces.
                  </p>
                </div>
                
                <div className="p-3.5 rounded-xl bg-violet-600/5 border border-violet-500/10 text-violet-300 text-[10px] leading-relaxed">
                  <span className="font-bold uppercase tracking-wider block mb-1 text-[9px] text-violet-400">Demo Environment</span>
                  This dashboard represents mock portfolios and demo assets created exclusively for verification of the Nexora AI Support Hub client experience.
                </div>

                <div className="space-y-1.5">
                  <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">Office Location</h4>
                  <p className="leading-tight text-slate-400">
                    100 Innovation Way, Suite 400<br />
                    Tech City, CA 94016
                  </p>
                </div>

                <div className="space-y-1.5">
                  <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">Supported Product Lines</h4>
                  <ul className="list-disc pl-4 space-y-1">
                    <li>Nexora Smart Hub controllers</li>
                    <li>Sleek Keyboard and Touchpads</li>
                    <li>Enterprise Workspace systems</li>
                  </ul>
                </div>
              </>
            ) : (
              <>
                <div className="space-y-3">
                  <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">Get In Touch</h4>
                  <div className="space-y-2">
                    <div>
                      <p className="text-[9px] text-slate-500 uppercase tracking-wider">Support Email</p>
                      <a href="mailto:support@nexoratech.demo" className="text-violet-400 hover:underline font-medium">
                        support@nexoratech.demo
                      </a>
                    </div>
                    <div>
                      <p className="text-[9px] text-slate-500 uppercase tracking-wider">Helpline Phone</p>
                      <p className="text-slate-300 font-medium">+1 (800) 555-0199</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-slate-500 uppercase tracking-wider">Operating Hours</p>
                      <p className="text-slate-300">Mon-Fri 8:00 AM - 6:00 PM PST</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 pt-2 border-t border-slate-800/80">
                  <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[10px]">Official Channels</h4>
                  <div className="flex flex-col gap-1.5">
                    <span>Website: <a href="https://www.nexoratech.demo" target="_blank" rel="noreferrer" className="text-violet-400 hover:underline">www.nexoratech.demo</a></span>
                    <span className="text-slate-500">Twitter: @nexora_tech (mock)</span>
                    <span className="text-slate-500">LinkedIn: /company/nexora (mock)</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
