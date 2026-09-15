"use client";

import React, { useState, useEffect, useRef } from "react";
import { Navbar } from "@/components/Navbar";
import { CascadeFlow } from "@/components/CascadeFlow";
import { CostAuditCard } from "@/components/CostAuditCard";
import { AuditLedger } from "@/components/AuditLedger";
import { FreeTierGuideModal } from "@/components/FreeTierGuideModal";
import { ChatResponse, QueryHistoryItem, AnalyticsSummary } from "@/types";
import {
  Send,
  Copy,
  Check,
  Bot,
  User,
  Plus,
  AlertCircle,
  PanelLeftClose,
  PanelLeft,
  Settings2,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
  timestamp: string;
}

const PRESETS = [
  {
    title: "Complicated Q&A (Escalate)",
    prompt:
      "Design a distributed raft consensus protocol for high-write financial ledger. Analyze split-brain trade-offs, latency invariants, and clock synchronization pitfalls.",
  },
  {
    title: "Simple FAQ (Direct)",
    prompt: "What is the boiling point of water at standard atmospheric pressure?",
  },
  {
    title: "Architectural Comparison",
    prompt:
      "Explain the deep concurrency differences between PostgreSQL Serializable Snapshot Isolation (SSI) and MySQL InnoDB Next-Key Locks during high-frequency range updates.",
  },
];

export default function Home() {
  const [provider, setProvider] = useState<string>("gemini");
  const [threshold, setThreshold] = useState<number>(0.75);
  const [forceEscalation, setForceEscalation] = useState<boolean>(false);
  const [forceTier1Only, setForceTier1Only] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<
    "playground" | "analytics" | "history"
  >("playground");
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null
  );
  const [displayedAnswer, setDisplayedAnswer] = useState<string>("");
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [settingsOpen, setSettingsOpen] = useState<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, displayedAnswer]);

  const streamText = (fullText: string, messageId: string) => {
    setDisplayedAnswer("");
    setIsStreaming(true);
    setStreamingMessageId(messageId);
    let index = 0;
    const chunkSize = Math.max(1, Math.floor(fullText.length / 80));
    const interval = setInterval(() => {
      index += chunkSize;
      if (index >= fullText.length) {
        setDisplayedAnswer(fullText);
        setIsStreaming(false);
        setStreamingMessageId(null);
        clearInterval(interval);
      } else {
        setDisplayedAnswer(fullText.slice(0, index));
      }
    }, 16);
  };

  const fetchAuditData = async () => {
    try {
      const historyRes = await fetch("/api/history");
      if (historyRes.ok) setHistory(await historyRes.json());
      const analyticsRes = await fetch("/api/analytics");
      if (analyticsRes.ok) setAnalytics(await analyticsRes.json());
      const providersRes = await fetch("/api/providers");
      if (providersRes.ok) {
        const pData = await providersRes.json();
        if (pData.default_provider && pData.default_provider !== "mock") {
          setProvider((curr) => (curr === "mock" ? pData.default_provider : curr));
        }
      }
    } catch {
      console.log("Backend offline or local simulation active");
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);
    setErrorMsg(null);
    setDisplayedAnswer("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const assistantId = `assistant-${Date.now()}`;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: userMsg.content,
          provider,
          confidence_threshold: threshold,
          force_escalation: forceEscalation,
          force_tier1_only: forceTier1Only,
        }),
      });

      if (!res.ok)
        throw new Error(`Server returned ${res.status}: ${res.statusText}`);

      const data: ChatResponse = await res.json();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: data.final_answer,
        response: data,
        timestamp: data.timestamp,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      streamText(data.final_answer, assistantId);
      fetchAuditData();
    } catch (err: unknown) {
      console.error("Chat API error:", err);
      const errText = err instanceof Error ? err.message : String(err);
      const errorMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: `Sorry, something went wrong. ${errText}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyAnswer = (text: string) => {
    navigator.clipboard.writeText(text);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  };

  const newChat = () => {
    setMessages([]);
    setInputValue("");
    setDisplayedAnswer("");
    setErrorMsg(null);
    setActiveTab("playground");
  };

  return (
    <div className="h-screen flex flex-col bg-[#212121]">
      {/* Top Navbar */}
      <Navbar
        provider={provider}
        setProvider={setProvider}
        onOpenGuide={() => setIsGuideOpen(true)}
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          if (tab !== "playground") setSidebarOpen(false);
        }}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        onNewChat={newChat}
      />

      <FreeTierGuideModal
        isOpen={isGuideOpen}
        onClose={() => setIsGuideOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          } md:translate-x-0 fixed md:static inset-y-0 left-0 z-30 w-64 bg-[#171717] border-r border-neutral-700 flex flex-col transition-transform duration-200 ease-in-out`}
        >
          <div className="flex items-center justify-between p-3 border-b border-neutral-700">
            <button
              onClick={newChat}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-neutral-600 text-sm text-neutral-200 hover:bg-neutral-800 transition w-full"
            >
              <Plus className="w-4 h-4" />
              New chat
            </button>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition md:hidden"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {messages.filter((m) => m.role === "user").length === 0 ? (
              <div className="px-3 py-8 text-center text-xs text-neutral-500">
                No conversations yet. Start a new chat!
              </div>
            ) : (
              messages
                .filter((m) => m.role === "user")
                .map((msg) => (
                  <button
                    key={msg.id}
                    onClick={() => setActiveTab("playground")}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-neutral-300 hover:bg-neutral-800 transition truncate"
                  >
                    {msg.content}
                  </button>
                ))
            )}
          </div>

          <div className="p-3 border-t border-neutral-700">
            <button
              onClick={() => setIsGuideOpen(true)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-neutral-400 hover:text-white hover:bg-neutral-800 transition w-full"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              Free Tier Keys Guide
            </button>
          </div>
        </aside>

        {/* Sidebar overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-20 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col min-w-0">
          {activeTab === "playground" ? (
            <>
              {/* Settings Panel (collapsible) */}
              {settingsOpen && (
                <div className="border-b border-neutral-700 bg-[#1a1a1a] px-4 py-3">
                  <div className="max-w-3xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <div className="space-y-1.5">
                      <label className="text-neutral-400 font-medium">
                        Escalation Threshold
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="range"
                          min="0.50"
                          max="0.95"
                          step="0.05"
                          value={threshold}
                          onChange={(e) =>
                            setThreshold(parseFloat(e.target.value))
                          }
                          className="flex-1 h-1 bg-neutral-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                        />
                        <span className="font-mono text-blue-400 font-bold w-10 text-right">
                          {threshold.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer text-neutral-300">
                        <input
                          type="checkbox"
                          checked={forceEscalation}
                          onChange={(e) => {
                            setForceEscalation(e.target.checked);
                            if (e.target.checked) setForceTier1Only(false);
                          }}
                          className="rounded bg-neutral-800 border-neutral-600 text-blue-500 focus:ring-blue-500"
                        />
                        Force Escalate
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer text-neutral-300">
                        <input
                          type="checkbox"
                          checked={forceTier1Only}
                          onChange={(e) => {
                            setForceTier1Only(e.target.checked);
                            if (e.target.checked) setForceEscalation(false);
                          }}
                          className="rounded bg-neutral-800 border-neutral-600 text-blue-500 focus:ring-blue-500"
                        />
                        Tier 1 Only
                      </label>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-neutral-400 font-medium">
                        Provider
                      </label>
                      <select
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                        className="w-full bg-neutral-800 border border-neutral-600 text-white rounded-lg px-3 py-1.5 text-xs outline-none"
                      >
                        <option value="mock">Simulation (Haiku &rarr; Sonnet)</option>
                        <option value="gemini">Gemini (Free Tier)</option>
                        <option value="groq">Groq (Free Tier)</option>
                        <option value="mistral">Mistral</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="openai">OpenAI</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto">
                {messages.length === 0 ? (
                  /* Empty state */
                  <div className="flex flex-col items-center justify-center h-full px-4">
                    <div className="w-12 h-12 rounded-full bg-blue-600/20 flex items-center justify-center mb-4">
                      <Bot className="w-6 h-6 text-blue-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-white mb-2">
                      How can I help you today?
                    </h2>
                    <p className="text-sm text-neutral-400 mb-8 text-center max-w-md">
                      Cost-aware cascading router. Queries go to low-cost
                      models first, escalated to frontier only when confidence
                      is low.
                    </p>

                    {/* Preset suggestions */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl w-full">
                      {PRESETS.map((preset, idx) => (
                        <button
                          key={idx}
                          onClick={() => setInputValue(preset.prompt)}
                          className="text-left p-4 rounded-xl border border-neutral-700 bg-[#2f2f2f] hover:bg-[#3a3a3a] transition group"
                        >
                          <div className="text-sm text-neutral-200 font-medium mb-1 group-hover:text-white transition">
                            {preset.title}
                          </div>
                          <div className="text-xs text-neutral-500 line-clamp-2">
                            {preset.prompt}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  /* Messages list */
                  <div className="max-w-3xl mx-auto w-full">
                    {messages.map((msg) => (
                      <div key={msg.id}>
                        {/* User message */}
                        {msg.role === "user" && (
                          <div className="flex justify-end px-4 py-6">
                            <div className="flex items-start gap-3 max-w-[85%]">
                              <div className="bg-[#2f2f2f] rounded-2xl px-4 py-3 text-sm text-neutral-100 whitespace-pre-wrap leading-relaxed">
                                {msg.content}
                              </div>
                              <div className="w-8 h-8 rounded-full bg-[#5436da] flex items-center justify-center shrink-0">
                                <User className="w-4 h-4 text-white" />
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Assistant message */}
                        {msg.role === "assistant" && (
                          <div className="px-4 py-6 bg-[#212121]">
                            <div className="max-w-3xl mx-auto flex items-start gap-3">
                              <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center shrink-0 mt-1">
                                <Bot className="w-4 h-4 text-white" />
                              </div>
                              <div className="flex-1 min-w-0 space-y-4">
                                {/* Model label */}
                                {msg.response && (
                                  <div className="flex items-center gap-2 text-xs text-neutral-400">
                                    <span className="font-medium text-neutral-300">
                                      {msg.response.served_by_model}
                                    </span>
                                    <span>&middot;</span>
                                    <span className="uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                      {msg.response.served_by_tier}
                                    </span>
                                    {msg.response.escalation.escalated && (
                                      <>
                                        <span>&middot;</span>
                                        <span className="uppercase text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                          Escalated
                                        </span>
                                      </>
                                    )}
                                  </div>
                                )}

                                {/* Answer text */}
                                <div className="text-sm text-neutral-100 leading-relaxed whitespace-pre-wrap">
                                  {streamingMessageId === msg.id
                                    ? displayedAnswer
                                    : msg.content}
                                  {streamingMessageId === msg.id && (
                                    <span className="inline-block w-2 h-4 bg-blue-400 ml-0.5 animate-pulse align-text-bottom" />
                                  )}
                                </div>

                                {/* Copy button */}
                                {streamingMessageId !== msg.id && (
                                  <div className="flex items-center gap-2 pt-1">
                                    <button
                                      onClick={() => copyAnswer(msg.content)}
                                      className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800 transition"
                                    >
                                      {isCopied ? (
                                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                                      ) : (
                                        <Copy className="w-3.5 h-3.5" />
                                      )}
                                      {isCopied ? "Copied" : "Copy"}
                                    </button>
                                  </div>
                                )}

                                {/* Cascade flow + Cost audit (collapsible details) */}
                                {msg.response && streamingMessageId !== msg.id && (
                                  <div className="mt-4 space-y-4">
                                    <CascadeFlow
                                      response={msg.response}
                                      isLoading={false}
                                      threshold={threshold}
                                    />
                                    <CostAuditCard response={msg.response} />
                                  </div>
                                )}

                                {/* Loading indicator */}
                                {streamingMessageId !== msg.id &&
                                  isLoading &&
                                  !msg.response &&
                                  msg.role === "assistant" && (
                                    <div className="flex items-center gap-2 text-neutral-400 text-sm">
                                      <div className="w-4 h-4 border-2 border-neutral-500 border-t-transparent rounded-full animate-spin" />
                                      Thinking...
                                    </div>
                                  )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Show loading message if waiting for response */}
                    {isLoading &&
                      !streamingMessageId &&
                      messages[messages.length - 1]?.role === "user" && (
                        <div className="px-4 py-6 bg-[#212121]">
                          <div className="max-w-3xl mx-auto flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center shrink-0">
                              <Bot className="w-4 h-4 text-white" />
                            </div>
                            <div className="flex items-center gap-2 text-neutral-400 text-sm pt-1">
                              <div className="w-4 h-4 border-2 border-neutral-500 border-t-transparent rounded-full animate-spin" />
                              Evaluating cascade pipeline...
                            </div>
                          </div>
                        </div>
                      )}

                    <div ref={chatEndRef} className="h-4" />
                  </div>
                )}
              </div>

              {/* Error message */}
              {errorMsg && (
                <div className="max-w-3xl mx-auto w-full px-4 pb-2">
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                </div>
              )}

              {/* Input Area */}
              <div className="border-t border-neutral-700 bg-[#212121] p-4">
                <form
                  onSubmit={handleSubmit}
                  className="max-w-3xl mx-auto relative"
                >
                  <div className="flex items-end gap-2 bg-[#2f2f2f] rounded-2xl border border-neutral-600 focus-within:border-neutral-500 transition px-4 py-3">
                    <textarea
                      ref={textareaRef}
                      value={inputValue}
                      onChange={handleTextareaInput}
                      onKeyDown={handleKeyDown}
                      rows={1}
                      placeholder="Message CostAware..."
                      className="flex-1 bg-transparent text-sm text-neutral-100 placeholder-neutral-500 outline-none resize-none leading-relaxed max-h-[200px]"
                    />
                    <button
                      type="submit"
                      disabled={isLoading || !inputValue.trim()}
                      className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-2 px-1">
                    <button
                      type="button"
                      onClick={() => setSettingsOpen(!settingsOpen)}
                      className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-300 transition"
                    >
                      <Settings2 className="w-3.5 h-3.5" />
                      {settingsOpen ? "Hide" : "Show"} settings
                    </button>
                    <span className="text-[10px] text-neutral-600">
                      Threshold: {threshold.toFixed(2)} &middot; Provider:{" "}
                      {provider}
                    </span>
                  </div>
                </form>
              </div>
            </>
          ) : (
            /* Analytics / History tabs */
            <div className="flex-1 overflow-y-auto p-4 sm:p-6">
              <AuditLedger
                history={history}
                analytics={analytics}
                onRefresh={fetchAuditData}
                isLoading={false}
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
