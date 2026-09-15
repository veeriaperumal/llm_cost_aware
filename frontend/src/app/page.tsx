"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { CascadeFlow } from "@/components/CascadeFlow";
import { CostAuditCard } from "@/components/CostAuditCard";
import { AuditLedger } from "@/components/AuditLedger";
import { FreeTierGuideModal } from "@/components/FreeTierGuideModal";
import { ChatResponse, QueryHistoryItem, AnalyticsSummary } from "@/types";
import { Send, Sparkles, Sliders, Play, Copy, Check, Info, Bot, CornerDownLeft, AlertCircle } from "lucide-react";

const PRESETS = [
  {
    title: "Complicated Q&A (Low Confidence ➔ Escalate)",
    prompt: "Design a distributed raft consensus protocol for high-write financial ledger. Analyze split-brain trade-offs, latency invariants, and clock synchronization pitfalls.",
    description: "Triggers Haiku confidence = 0.61 (< 0.75) ➔ ESCALATE (low_confidence) ➔ Sonnet resolution"
  },
  {
    title: "Simple FAQ (High Confidence ➔ Haiku Direct)",
    prompt: "What is the boiling point of water at standard atmospheric pressure?",
    description: "Haiku confidence = 0.94 (&ge; 0.75) ➔ Solved at Tier 1 with 100% Sonnet budget saved"
  },
  {
    title: "Architectural Comparison (Escalation Case)",
    prompt: "Explain the deep concurrency differences between PostgreSQL Serializable Snapshot Isolation (SSI) and MySQL InnoDB Next-Key Locks during high-frequency range updates.",
    description: "Evaluates subtle database concurrency nuances requiring Tier 2 depth"
  }
];

export default function Home() {
  const [provider, setProvider] = useState<string>("gemini");
  const [prompt, setPrompt] = useState<string>(PRESETS[0].prompt);
  const [threshold, setThreshold] = useState<number>(0.75);
  const [forceEscalation, setForceEscalation] = useState<boolean>(false);
  const [forceTier1Only, setForceTier1Only] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"playground" | "analytics" | "history">("playground");
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(false);

  const [currentResponse, setCurrentResponse] = useState<ChatResponse | null>(null);
  const [displayedAnswer, setDisplayedAnswer] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Smooth typewriter streaming animation for incoming answers
  const streamText = (fullText: string) => {
    setDisplayedAnswer("");
    setIsStreaming(true);
    let index = 0;
    const chunkSize = Math.max(1, Math.floor(fullText.length / 80)); // Dynamic speed based on length
    const interval = setInterval(() => {
      index += chunkSize;
      if (index >= fullText.length) {
        setDisplayedAnswer(fullText);
        setIsStreaming(false);
        clearInterval(interval);
      } else {
        setDisplayedAnswer(fullText.slice(0, index));
      }
    }, 16);
  };

  // Fetch initial history & analytics
  const fetchAuditData = async () => {
    try {
      const historyRes = await fetch("/api/history");
      if (historyRes.ok) {
        const hData = await historyRes.json();
        setHistory(hData);
      }

      const analyticsRes = await fetch("/api/analytics");
      if (analyticsRes.ok) {
        const aData = await analyticsRes.json();
        setAnalytics(aData);
      }
    } catch (err) {
      console.log("Backend offline or local simulation active");
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);
    setDisplayedAnswer("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          provider,
          confidence_threshold: threshold,
          force_escalation: forceEscalation,
          force_tier1_only: forceTier1Only
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}: ${res.statusText}`);
      }

      const data: ChatResponse = await res.json();
      setCurrentResponse(data);
      streamText(data.final_answer);
      fetchAuditData();
    } catch (err: any) {
      console.error(err);
      setErrorMsg("Could not connect to backend. Please ensure the backend server is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  };

  const copyAnswer = () => {
    if (!currentResponse?.final_answer) return;
    navigator.clipboard.writeText(currentResponse.final_answer);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar
        provider={provider}
        setProvider={setProvider}
        onOpenGuide={() => setIsGuideOpen(true)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <FreeTierGuideModal isOpen={isGuideOpen} onClose={() => setIsGuideOpen(false)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-2 max-w-3xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-cyan-400 tracking-tight">
            Cost-Aware Cascading Router & Escalation
          </h1>
          <p className="text-sm sm:text-base text-slate-400">
            Routes queries to low-cost Tier 1 first (Haiku / Flash). If confidence falls below threshold (e.g. 0.61), dynamically escalates to Tier 2 (Sonnet) and logs the spend justification.
          </p>
        </div>

        {/* Tab Content */}
        {activeTab === "playground" && (
          <div className="space-y-8">
            {/* Input & Control Panel */}
            <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-slate-800 space-y-5">
              {/* Presets Row */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Play className="w-3.5 h-3.5 text-cyan-400" /> Quick Test Presets:
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
                  {PRESETS.map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setPrompt(preset.prompt)}
                      className={`text-left p-3 rounded-xl border transition-all ${
                        prompt === preset.prompt
                          ? "bg-blue-600/20 border-blue-500/50 text-white"
                          : "bg-slate-900/70 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-800/60"
                      }`}
                    >
                      <div className="text-xs font-bold text-slate-200 mb-1">{preset.title}</div>
                      <div className="text-[10px] text-slate-400 line-clamp-2">{preset.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt Textarea */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                    placeholder="Enter any complex question, reasoning query, or simple factoid..."
                    className="w-full rounded-xl bg-slate-950/80 border border-slate-700/80 p-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition font-sans"
                  />
                </div>

                {/* Control Sliders & Toggles */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-slate-800/80 text-xs">
                  {/* Threshold Slider */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-slate-300 font-semibold">
                      <span className="flex items-center gap-1">
                        <Sliders className="w-3.5 h-3.5 text-cyan-400" /> Escalation Threshold:
                      </span>
                      <span className="font-mono text-cyan-400 font-bold">{threshold.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min="0.50"
                      max="0.95"
                      step="0.05"
                      value={threshold}
                      onChange={(e) => setThreshold(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                    />
                    <div className="text-[10px] text-slate-500">Escalates to Sonnet if Tier 1 confidence &lt; {threshold.toFixed(2)}</div>
                  </div>

                  {/* Force Escalation Toggle */}
                  <div className="flex items-center justify-between sm:justify-center gap-2 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <label className="text-slate-300 cursor-pointer flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={forceEscalation}
                        onChange={(e) => {
                          setForceEscalation(e.target.checked);
                          if (e.target.checked) setForceTier1Only(false);
                        }}
                        className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-blue-500"
                      />
                      <span>Force Escalate (Tier 2)</span>
                    </label>
                  </div>

                  {/* Force Tier 1 Only Toggle */}
                  <div className="flex items-center justify-between sm:justify-center gap-2 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                    <label className="text-slate-300 cursor-pointer flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={forceTier1Only}
                        onChange={(e) => {
                          setForceTier1Only(e.target.checked);
                          if (e.target.checked) setForceEscalation(false);
                        }}
                        className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-blue-500"
                      />
                      <span>Bypass Escalation (Tier 1 Only)</span>
                    </label>
                  </div>
                </div>

                {errorMsg && (
                  <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                )}

                {/* Submit Button */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={isLoading || !prompt.trim()}
                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-blue-600/30 flex items-center gap-2 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Evaluating Cascade Pipeline...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        <span>Run Cascading Pipeline</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Cascade Flow Visualizer */}
            <CascadeFlow response={currentResponse} isLoading={isLoading} threshold={threshold} />

            {/* Final Answer Display */}
            {currentResponse && (
              <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-slate-800 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold">
                      <Bot className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-white">Synthesized Authoritative Answer</h3>
                        {isStreaming && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold animate-pulse border border-cyan-500/30">
                            Streaming Response...
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Served by <strong className="text-cyan-300">{currentResponse.served_by_model}</strong> ({currentResponse.served_by_tier.toUpperCase()})
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={copyAnswer}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:text-white transition"
                  >
                    {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{isCopied ? "Copied" : "Copy Answer"}</span>
                  </button>
                </div>

                <div className="prose prose-invert max-w-none text-slate-100 text-sm leading-relaxed whitespace-pre-wrap font-sans bg-slate-950/80 p-5 rounded-xl border border-slate-800/80 shadow-inner">
                  {displayedAnswer || currentResponse.final_answer}
                  {isStreaming && <span className="inline-block w-2 h-4 bg-cyan-400 ml-1 animate-pulse"></span>}
                </div>
              </div>
            )}

            {/* Cost & ROI Audit Breakdown */}
            <CostAuditCard response={currentResponse} />
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === "analytics" && (
          <AuditLedger
            history={history}
            analytics={analytics}
            onRefresh={fetchAuditData}
            isLoading={false}
          />
        )}

        {/* Audit History Tab */}
        {activeTab === "history" && (
          <AuditLedger
            history={history}
            analytics={analytics}
            onRefresh={fetchAuditData}
            isLoading={false}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>CostAware AI &copy; 2026 &mdash; Cascading Router with Dynamic Confidence Gates</span>
          <span>FastAPI Backend + Next.js App Router</span>
        </div>
      </footer>
    </div>
  );
}
