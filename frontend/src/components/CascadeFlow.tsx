"use client";

import React from "react";
import { ChatResponse } from "../types";
import { ArrowDown, AlertTriangle, CheckCircle2, DollarSign, Sparkles, ShieldAlert, Cpu, ArrowRight } from "lucide-react";

interface CascadeFlowProps {
  response: ChatResponse | null;
  isLoading: boolean;
  threshold: number;
}

export const CascadeFlow: React.FC<CascadeFlowProps> = ({ response, isLoading, threshold }) => {
  if (isLoading) {
    return (
      <div className="glass-panel rounded-2xl p-8 border border-slate-800 text-center animate-pulse">
        <div className="flex flex-col items-center justify-center space-y-4 py-8">
          <div className="w-12 h-12 rounded-full border-4 border-cyan-500 border-t-transparent animate-spin"></div>
          <div className="text-slate-300 font-semibold text-sm">Executing Multi-Tier Cascade Pipeline...</div>
          <div className="text-xs text-slate-500 max-w-sm">
            Step 1: Running Tier 1 (Haiku) ➔ Assessing self-confidence ➔ Checking threshold ({threshold.toFixed(2)})...
          </div>
        </div>
      </div>
    );
  }

  if (!response) {
    return (
      <div className="glass-panel rounded-2xl p-8 border border-slate-800 text-center">
        <div className="py-12">
          <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-4">
            <Cpu className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-white mb-1">Cascading LLM Visual Pipeline</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mb-4">
            Submit a prompt or select a preset to watch the routing decisions, confidence gating, escalation reasons, and spend auditing live.
          </p>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            Pipeline Ready (Threshold: {threshold.toFixed(2)})
          </div>
        </div>
      </div>
    );
  }

  const isEscalated = response.escalation.escalated;
  const confidence = response.confidence;
  const isHighConfidence = confidence >= threshold;
  const tier1Trace = response.traces.find((t) => t.tier === "tier1");
  const tier2Trace = response.traces.find((t) => t.tier === "tier2");

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-slate-800 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Execution Cascade Flow</h3>
            <p className="text-[11px] text-slate-400">Live request tracing and confidence evaluation gate</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 font-mono">Latency: {response.total_latency_ms}ms</span>
          <span
            className={`text-[11px] px-2.5 py-1 rounded-full font-bold border ${
              isEscalated
                ? "bg-amber-500/10 text-amber-300 border-amber-500/30 glow-amber"
                : "bg-emerald-500/10 text-emerald-300 border-emerald-500/30 glow-emerald"
            }`}
          >
            {isEscalated ? "ESCALATED TO TIER 2" : "SOLVED AT TIER 1"}
          </span>
        </div>
      </div>

      {/* Interactive Visual Graph Pipeline */}
      <div className="flex flex-col items-center space-y-3 py-2">
        {/* Step 1: User Prompt Node */}
        <div className="w-full max-w-xl p-3.5 rounded-xl bg-slate-900/90 border border-slate-700/80 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300">
              👤
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider font-bold text-slate-400">User Query</div>
              <div className="text-xs font-semibold text-slate-100 line-clamp-1">"{response.prompt}"</div>
            </div>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Input</span>
        </div>

        {/* Connector Arrow */}
        <div className="flex items-center justify-center text-slate-500">
          <ArrowDown className="w-4 h-4" />
        </div>

        {/* Step 2: Tier 1 (Haiku / Flash / Fast) Node */}
        <div
          className={`w-full max-w-xl p-4 rounded-xl border transition-all ${
            isHighConfidence
              ? "bg-emerald-950/20 border-emerald-500/40 glow-emerald"
              : "bg-slate-900/90 border-slate-700/80"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                TIER 1
              </span>
              <span className="text-xs font-bold text-white">{tier1Trace?.model_name || "Haiku"}</span>
            </div>
            <div className="text-[11px] font-mono text-slate-400">
              Cost: <span className="text-slate-200 font-semibold">${tier1Trace?.cost_usd.toFixed(6)}</span>
            </div>
          </div>

          {/* Confidence Meter */}
          <div className="mt-3 p-3 rounded-lg bg-slate-950/70 border border-slate-800/80">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-slate-400 font-medium">Self-Evaluated Confidence:</span>
              <span
                className={`font-mono font-extrabold ${
                  isHighConfidence ? "text-emerald-400" : "text-amber-400"
                }`}
              >
                {confidence.toFixed(2)} / 1.00
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  isHighConfidence
                    ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                    : "bg-gradient-to-r from-rose-500 to-amber-500"
                }`}
                style={{ width: `${Math.min(100, Math.max(5, confidence * 100))}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
              <span>0.00 (Uncertain)</span>
              <span className="text-blue-400 font-semibold">Threshold: {threshold.toFixed(2)}</span>
              <span>1.00 (Certain)</span>
            </div>
          </div>

          {/* Uncertainty reasons if low confidence */}
          {tier1Trace?.uncertainty_reasons && tier1Trace.uncertainty_reasons.length > 0 && (
            <div className="mt-2.5 text-[11px] text-amber-300/90 bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
              <div className="font-semibold mb-0.5 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Tier 1 Uncertainty Flags:
              </div>
              <ul className="list-disc list-inside space-y-0.5 text-[10px] text-amber-200/80">
                {tier1Trace.uncertainty_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Step 3: Decision Gate / Escalation Node */}
        {isEscalated ? (
          <>
            <div className="flex items-center justify-center text-amber-400">
              <ArrowDown className="w-4 h-4 animate-bounce" />
            </div>

            <div className="w-full max-w-xl p-4 rounded-xl bg-gradient-to-r from-amber-950/40 via-slate-900/90 to-amber-950/40 border border-amber-500/50 glow-amber">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-extrabold uppercase tracking-wider text-amber-400">
                    ESCALATE GATE TRIGGERED
                  </span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  reason = "{response.escalation.reason}"
                </span>
              </div>
              <p className="text-xs text-slate-300">
                {response.escalation.explanation || `Confidence ${confidence.toFixed(2)} is lower than threshold ${threshold.toFixed(2)}.`}
              </p>
            </div>

            <div className="flex items-center justify-center text-slate-500">
              <ArrowDown className="w-4 h-4" />
            </div>

            {/* Step 4: Tier 2 (Sonnet / Frontier) Node */}
            <div className="w-full max-w-xl p-4 rounded-xl bg-blue-950/20 border border-blue-500/40 glow-blue">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    TIER 2 (FRONTIER)
                  </span>
                  <span className="text-xs font-bold text-white">{tier2Trace?.model_name || "Sonnet"}</span>
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  Cost: <span className="text-blue-300 font-semibold">${tier2Trace?.cost_usd.toFixed(6)}</span>
                </div>
              </div>
              <div className="text-xs text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                <span className="text-blue-400 font-semibold">Context Passed:</span> User Prompt + Haiku Draft + Escalation Rationale. Synthesized high-precision authoritative resolution.
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center justify-center text-emerald-400">
              <ArrowDown className="w-4 h-4" />
            </div>
            <div className="w-full max-w-xl p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-500/40 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <div>
                  <div className="text-xs font-bold text-white">Tier 1 Confidence Sufficient ({confidence.toFixed(2)} &ge; {threshold.toFixed(2)})</div>
                  <div className="text-[11px] text-emerald-300">Escalation bypassed. Zero unnecessary frontier spend.</div>
                </div>
              </div>
              <span className="text-[10px] px-2 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                100% BUDGET SAVED
              </span>
            </div>
          </>
        )}

        {/* Step 5: Spend Rationale Ledger Banner */}
        <div className="w-full max-w-xl mt-3 p-3.5 rounded-xl bg-slate-900/95 border border-slate-800 text-xs text-slate-300 flex items-start gap-3">
          <DollarSign className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-white">Audit Ledger Explanation: </span>
            <span className="text-slate-300">{response.cost_breakdown.spend_justification}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
