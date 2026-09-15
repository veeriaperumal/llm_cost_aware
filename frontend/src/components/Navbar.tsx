"use client";

import React from "react";
import { Cpu, DollarSign, HelpCircle, Layers, ShieldCheck, Sparkles, Activity } from "lucide-react";

interface NavbarProps {
  provider: string;
  setProvider: (p: string) => void;
  onOpenGuide: () => void;
  activeTab: "playground" | "analytics" | "history";
  setActiveTab: (tab: "playground" | "analytics" | "history") => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  provider,
  setProvider,
  onOpenGuide,
  activeTab,
  setActiveTab
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white font-black text-xl">
            ⚡
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg text-white tracking-tight">CostAware</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-400/30 text-cyan-300">
                Cascading Router
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Multi-Tier Confidence Gate & Spend Audit</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="hidden md:flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("playground")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              activeTab === "playground"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" /> Pipeline Playground
          </button>
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              activeTab === "analytics"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity className="w-3.5 h-3.5" /> ROI Analytics
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              activeTab === "history"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" /> Audit Ledger
          </button>
        </div>

        {/* Provider Switcher & Free Key Guide */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-400 font-medium">Provider:</span>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="bg-transparent text-white font-semibold outline-none cursor-pointer text-xs"
            >
              <option value="mock" className="bg-slate-900 text-white">Simulation (Haiku ➔ Sonnet)</option>
              <option value="gemini" className="bg-slate-900 text-white">Gemini (Flash ➔ Pro) [Free Tier]</option>
              <option value="groq" className="bg-slate-900 text-white">Groq (8B ➔ 70B) [Free Tier]</option>
              <option value="mistral" className="bg-slate-900 text-white">Mistral (Small ➔ Large)</option>
              <option value="anthropic" className="bg-slate-900 text-white">Anthropic (Haiku ➔ Sonnet)</option>
              <option value="openai" className="bg-slate-900 text-white">OpenAI (Mini ➔ 4o)</option>
            </select>
          </div>

          <button
            onClick={onOpenGuide}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-xs font-medium text-slate-300 hover:text-white transition"
          >
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" /> Free Tier Keys?
          </button>
        </div>
      </div>
    </header>
  );
};
