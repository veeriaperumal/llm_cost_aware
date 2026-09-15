"use client";

import React from "react";
import { ChatResponse } from "../types";
import { DollarSign, TrendingDown, Layers, Zap, Scale, FileText, Check } from "lucide-react";

interface CostAuditCardProps {
  response: ChatResponse | null;
}

export const CostAuditCard: React.FC<CostAuditCardProps> = ({ response }) => {
  if (!response) return null;

  const { cost_breakdown, traces, escalation } = response;
  const isEscalated = escalation.escalated;

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-slate-800 space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
            <DollarSign className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Cost & Financial ROI Audit</h3>
            <p className="text-[11px] text-slate-400">Comparing cascading cost vs always-running Sonnet baseline</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs">
          <Scale className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-slate-400">Savings:</span>
          <span className="font-bold text-emerald-400 font-mono">
            {cost_breakdown.savings_percent > 0 ? `+${cost_breakdown.savings_percent}%` : `${cost_breakdown.savings_percent}%`}
          </span>
        </div>
      </div>

      {/* 4-Column Stat Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Tier 1 Spend */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Tier 1 Spend</div>
          <div className="text-lg font-black text-white font-mono">
            ${cost_breakdown.tier1_cost_usd.toFixed(6)}
          </div>
          <div className="text-[10px] text-cyan-400 mt-1">Preliminary Gate</div>
        </div>

        {/* Tier 2 Spend */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Tier 2 Spend</div>
          <div className="text-lg font-black text-white font-mono">
            ${cost_breakdown.tier2_cost_usd.toFixed(6)}
          </div>
          <div className="text-[10px] text-blue-400 mt-1">
            {isEscalated ? "Escalation Incurred" : "$0.00 (Bypassed)"}
          </div>
        </div>

        {/* Total Cost Incurred */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Actual Total Cost</div>
          <div className="text-lg font-black text-amber-300 font-mono">
            ${cost_breakdown.total_cost_usd.toFixed(6)}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Total query execution</div>
        </div>

        {/* Baseline Sonnet-Only Cost */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Baseline (Sonnet Only)</div>
          <div className="text-lg font-black text-slate-300 font-mono line-through">
            ${cost_breakdown.baseline_sonnet_cost_usd.toFixed(6)}
          </div>
          <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1 font-semibold">
            <TrendingDown className="w-3 h-3" /> Saved ${Math.max(0, cost_breakdown.savings_usd).toFixed(6)}
          </div>
        </div>
      </div>

      {/* Executive Financial Rationale ("Why we spent the extra money") */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 via-slate-800/60 to-slate-900 border border-slate-700/80">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-200 mb-2">
          <FileText className="w-4 h-4 text-cyan-400" />
          <span>Financial Audit Rationale (Recorded in Ledger):</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          {cost_breakdown.spend_justification}
        </p>
      </div>

      {/* Model Traces Breakdown Table */}
      <div className="space-y-2">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">Per-Model Execution Tokens</div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2 px-3 font-semibold">Tier</th>
                <th className="py-2 px-3 font-semibold">Model</th>
                <th className="py-2 px-3 font-semibold">Input Tokens</th>
                <th className="py-2 px-3 font-semibold">Output Tokens</th>
                <th className="py-2 px-3 font-semibold">Total Tokens</th>
                <th className="py-2 px-3 font-semibold">Cost</th>
                <th className="py-2 px-3 font-semibold">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {traces.map((t, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30">
                  <td className="py-2 px-3">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        t.tier === "tier1" ? "bg-cyan-500/20 text-cyan-300" : "bg-blue-500/20 text-blue-300"
                      }`}
                    >
                      {t.tier.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-sans text-white font-medium">{t.model_name}</td>
                  <td className="py-2 px-3 text-slate-300">{t.tokens.input_tokens}</td>
                  <td className="py-2 px-3 text-slate-300">{t.tokens.output_tokens}</td>
                  <td className="py-2 px-3 text-slate-200 font-bold">{t.tokens.total_tokens}</td>
                  <td className="py-2 px-3 text-emerald-400 font-bold">${t.cost_usd.toFixed(6)}</td>
                  <td className="py-2 px-3 text-slate-400">{t.latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
