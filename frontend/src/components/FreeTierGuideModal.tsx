"use client";

import React from "react";
import { X, CheckCircle2, AlertTriangle, ExternalLink, Key, Zap, ShieldCheck } from "lucide-react";

interface FreeTierGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FreeTierGuideModal: React.FC<FreeTierGuideModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl glass-panel p-6 sm:p-8 border border-slate-700 bg-slate-900/95 text-slate-100 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white">
            <Key className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">API Key & Free Tier Guide</h2>
            <p className="text-sm text-slate-400">Review of Free vs Paid LLM Provider APIs for Testing this Cascading Router</p>
          </div>
        </div>

        {/* Free Tier Providers Section */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-2 mb-3">
            <CheckCircle2 className="w-4 h-4" /> 100% Free Tier Available (Recommended for Zero-Cost Testing)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Google Gemini */}
            <div className="p-4 rounded-xl bg-slate-800/80 border border-emerald-500/30 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-white">Google Gemini</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold">FREE</span>
                </div>
                <p className="text-xs text-slate-300 mb-2">
                  Generous free tier on Google AI Studio (up to 15 RPM for Flash & Pro).
                </p>
                <div className="text-[11px] text-slate-400 space-y-1 mb-3">
                  <div>• Tier 1: <span className="text-cyan-300">Gemini 1.5 Flash</span></div>
                  <div>• Tier 2: <span className="text-blue-300">Gemini 1.5 Pro</span></div>
                </div>
              </div>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1 mt-2"
              >
                Get Gemini Key <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {/* Groq */}
            <div className="p-4 rounded-xl bg-slate-800/80 border border-emerald-500/30 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-white">Groq Cloud</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold">FREE</span>
                </div>
                <p className="text-xs text-slate-300 mb-2">
                  Fastest inference LPU with high rate limits for open-weights models.
                </p>
                <div className="text-[11px] text-slate-400 space-y-1 mb-3">
                  <div>• Tier 1: <span className="text-cyan-300">Llama 3.1 8B</span></div>
                  <div>• Tier 2: <span className="text-blue-300">Llama 3.3 70B</span></div>
                </div>
              </div>
              <a
                href="https://console.groq.com/keys"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1 mt-2"
              >
                Get Groq Key <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {/* Mistral */}
            <div className="p-4 rounded-xl bg-slate-800/80 border border-emerald-500/30 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-white">Mistral AI</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold">FREE TRIAL</span>
                </div>
                <p className="text-xs text-slate-300 mb-2">
                  Free tier / credits available on La Plateforme for development.
                </p>
                <div className="text-[11px] text-slate-400 space-y-1 mb-3">
                  <div>• Tier 1: <span className="text-cyan-300">Mistral Small</span></div>
                  <div>• Tier 2: <span className="text-blue-300">Mistral Large</span></div>
                </div>
              </div>
              <a
                href="https://console.mistral.ai/"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1 mt-2"
              >
                Get Mistral Key <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>

        {/* Paid Providers Section */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4" /> Commercial / Paid APIs (No Free Tier)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Anthropic */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-amber-500/30">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-white">Anthropic (Claude)</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold">PAID ONLY</span>
              </div>
              <p className="text-xs text-slate-300 mb-2">
                Anthropic does <strong>not</strong> have a permanent free tier. Requires a minimum $5 prepaid credit deposit to make API calls.
              </p>
              <div className="text-[11px] text-slate-400">
                • Tier 1: <span className="text-slate-200">Claude 3.5 Haiku</span> ($0.80/M in, $4.00/M out)<br />
                • Tier 2: <span className="text-slate-200">Claude 3.5 Sonnet</span> ($3.00/M in, $15.00/M out)
              </div>
            </div>

            {/* OpenAI */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-amber-500/30">
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-white">OpenAI</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold">PAID ONLY</span>
              </div>
              <p className="text-xs text-slate-300 mb-2">
                OpenAI requires prepaid API credits (usage tier 1+). Free trial credits are rarely granted or expire quickly.
              </p>
              <div className="text-[11px] text-slate-400">
                • Tier 1: <span className="text-slate-200">GPT-4o-mini</span> ($0.15/M in, $0.60/M out)<br />
                • Tier 2: <span className="text-slate-200">GPT-4o</span> ($2.50/M in, $10.00/M out)
              </div>
            </div>
          </div>
        </div>

        {/* Offline Simulated Mode */}
        <div className="p-4 rounded-xl bg-blue-950/40 border border-blue-500/30 flex items-start gap-3">
          <Zap className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-300">
            <span className="font-semibold text-white">Built-in Simulated Mode (Active by default):</span> You can test and demonstrate the exact Haiku (confidence = 0.61) ➔ ESCALATE (low_confidence) ➔ Sonnet workflow instantly without supplying any API keys!
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition"
          >
            Got it, Close
          </button>
        </div>
      </div>
    </div>
  );
};
