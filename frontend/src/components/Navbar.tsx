"use client";

import React from "react";
import { PanelLeft, Sparkles, Activity, Layers, HelpCircle } from "lucide-react";

interface NavbarProps {
  provider: string;
  setProvider: (p: string) => void;
  onOpenGuide: () => void;
  activeTab: "playground" | "analytics" | "history";
  setActiveTab: (tab: "playground" | "analytics" | "history") => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  onNewChat: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  provider,
  setProvider,
  onOpenGuide,
  activeTab,
  setActiveTab,
  sidebarOpen,
  setSidebarOpen,
  onNewChat,
}) => {
  return (
    <header className="flex items-center justify-between h-14 px-4 bg-[#212121] border-b border-neutral-700 shrink-0">
      {/* Left: Sidebar toggle + Brand */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition"
        >
          <PanelLeft className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">
            ⚡
          </div>
          <span className="font-semibold text-sm text-white hidden sm:block">
            CostAware
          </span>
        </div>
      </div>

      {/* Center: Tab Navigation */}
      <nav className="flex items-center gap-1 bg-[#2f2f2f] p-1 rounded-lg">
        <button
          onClick={() => setActiveTab("playground")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
            activeTab === "playground"
              ? "bg-neutral-700 text-white"
              : "text-neutral-400 hover:text-neutral-200"
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Playground</span>
        </button>
        <button
          onClick={() => setActiveTab("analytics")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
            activeTab === "analytics"
              ? "bg-neutral-700 text-white"
              : "text-neutral-400 hover:text-neutral-200"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Analytics</span>
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
            activeTab === "history"
              ? "bg-neutral-700 text-white"
              : "text-neutral-400 hover:text-neutral-200"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Audit Ledger</span>
        </button>
      </nav>

      {/* Right: Provider + Guide */}
      <div className="flex items-center gap-2">
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="bg-[#2f2f2f] border border-neutral-600 text-neutral-200 rounded-lg px-2.5 py-1.5 text-xs outline-none cursor-pointer hidden sm:block font-medium"
        >
          <option value="gemini">✨ Gemini (Live)</option>
          <option value="groq">⚡ Groq (Live)</option>
          <option value="auto">🎯 Auto (Pareto Optimal)</option>
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="mistral">Mistral</option>
          <option value="mock">Simulation (Offline)</option>
        </select>
        <button
          onClick={onOpenGuide}
          className="p-2 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition"
          title="Free Tier Keys Guide"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
