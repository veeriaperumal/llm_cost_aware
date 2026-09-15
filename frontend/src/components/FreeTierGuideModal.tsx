"use client";

import React from "react";
import { X, CheckCircle2, AlertTriangle, ExternalLink, Key, Zap } from "lucide-react";

interface FreeTierGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FreeTierGuideModal: React.FC<FreeTierGuideModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl bg-[#2f2f2f] border border-neutral-700 p-5 sm:p-6 text-neutral-100 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-700 transition"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400">
            <Key className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold">API Key Guide</h2>
            <p className="text-xs text-neutral-400">
              Free vs Paid LLM Provider APIs
            </p>
          </div>
        </div>

        {/* Free Providers */}
        <div className="mb-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5 mb-3">
            <CheckCircle2 className="w-3.5 h-3.5" /> Free Tier (Recommended)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {[
              {
                name: "Google Gemini",
                tier1: "Gemini 1.5 Flash",
                tier2: "Gemini 1.5 Pro",
                link: "https://aistudio.google.com/app/apikey",
              },
              {
                name: "Groq Cloud",
                tier1: "Llama 3.1 8B",
                tier2: "Llama 3.3 70B",
                link: "https://console.groq.com/keys",
              },
              {
                name: "Mistral AI",
                tier1: "Mistral Small",
                tier2: "Mistral Large",
                link: "https://console.mistral.ai/",
              },
            ].map((p) => (
              <div
                key={p.name}
                className="p-3 rounded-lg bg-neutral-800 border border-emerald-500/30"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-sm text-white">
                    {p.name}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                    FREE
                  </span>
                </div>
                <div className="text-[11px] text-neutral-400 mb-2 space-y-0.5">
                  <div>
                    T1: <span className="text-cyan-300">{p.tier1}</span>
                  </div>
                  <div>
                    T2: <span className="text-blue-300">{p.tier2}</span>
                  </div>
                </div>
                <a
                  href={p.link}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                >
                  Get Key <ExternalLink className="w-2.5 h-2.5" />
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* Paid Providers */}
        <div className="mb-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1.5 mb-3">
            <AlertTriangle className="w-3.5 h-3.5" /> Paid Only
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div className="p-3 rounded-lg bg-neutral-800/50 border border-amber-500/30">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-sm text-white">Anthropic</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                  PAID
                </span>
              </div>
              <div className="text-[11px] text-neutral-400">
                T1: Haiku ($0.80/M) &middot; T2: Sonnet ($3.00/M)
              </div>
            </div>
            <div className="p-3 rounded-lg bg-neutral-800/50 border border-amber-500/30">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-sm text-white">OpenAI</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                  PAID
                </span>
              </div>
              <div className="text-[11px] text-neutral-400">
                T1: GPT-4o-mini ($0.15/M) &middot; T2: GPT-4o ($2.50/M)
              </div>
            </div>
          </div>
        </div>

        {/* Simulated Mode */}
        <div className="p-3 rounded-lg bg-blue-950/40 border border-blue-500/30 flex items-start gap-2 mb-5">
          <Zap className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <div className="text-xs text-neutral-300">
            <span className="font-semibold text-white">Simulated Mode:</span>{" "}
            Test the full pipeline without any API keys. Active by default.
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
