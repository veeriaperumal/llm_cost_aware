"use client";

import React from "react";
import { ChatResponse } from "../types";
import { DollarSign, TrendingDown, Scale } from "lucide-react";

interface CostAuditCardProps {
  response: ChatResponse | null;
}

export const CostAuditCard: React.FC<CostAuditCardProps> = ({ response }) => {
  if (!response) return null;

  const { cost_breakdown, traces, escalation } = response;
  const isEscalated = escalation.escalated;

  return (
    <div className="rounded-xl border border-neutral-700 bg-[#2f2f2f] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold text-neutral-200">
            Cost Audit
          </span>
        </div>
        <div className="flex items-center gap-1 text-[10px]">
          <Scale className="w-3 h-3 text-blue-400" />
          <span className="text-neutral-400">Savings:</span>
          <span className="font-bold text-emerald-400 font-mono">
            {cost_breakdown.savings_percent > 0
              ? `+${cost_breakdown.savings_percent}%`
              : `${cost_breakdown.savings_percent}%`}
          </span>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="p-2.5 rounded-lg bg-neutral-800 border border-neutral-700">
            <div className="text-[10px] text-neutral-500 uppercase font-medium">
              Tier 1
            </div>
            <div className="text-sm font-bold text-neutral-100 font-mono">
              ${cost_breakdown.tier1_cost_usd.toFixed(6)}
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-neutral-800 border border-neutral-700">
            <div className="text-[10px] text-neutral-500 uppercase font-medium">
              Tier 2
            </div>
            <div className="text-sm font-bold text-neutral-100 font-mono">
              ${cost_breakdown.tier2_cost_usd.toFixed(6)}
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-neutral-800 border border-neutral-700">
            <div className="text-[10px] text-neutral-500 uppercase font-medium">
              Total
            </div>
            <div className="text-sm font-bold text-amber-300 font-mono">
              ${cost_breakdown.total_cost_usd.toFixed(6)}
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-neutral-800 border border-neutral-700">
            <div className="text-[10px] text-neutral-500 uppercase font-medium">
              Baseline
            </div>
            <div className="text-sm font-bold text-neutral-400 font-mono line-through">
              ${cost_breakdown.baseline_sonnet_cost_usd.toFixed(6)}
            </div>
            <div className="text-[10px] text-emerald-400 flex items-center gap-0.5">
              <TrendingDown className="w-2.5 h-2.5" />
              Saved ${Math.max(0, cost_breakdown.savings_usd).toFixed(6)}
            </div>
          </div>
        </div>

        {/* Model traces */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[11px]">
            <thead>
              <tr className="border-b border-neutral-700 text-neutral-500">
                <th className="py-1.5 px-2 font-medium">Tier</th>
                <th className="py-1.5 px-2 font-medium">Model</th>
                <th className="py-1.5 px-2 font-medium text-right">Tokens</th>
                <th className="py-1.5 px-2 font-medium text-right">Cost</th>
                <th className="py-1.5 px-2 font-medium text-right">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-700/50">
              {traces.map((t, idx) => (
                <tr key={idx} className="text-neutral-300">
                  <td className="py-1.5 px-2">
                    <span
                      className={`px-1 py-0.5 rounded text-[9px] font-bold ${
                        t.tier === "tier1"
                          ? "bg-cyan-500/20 text-cyan-300"
                          : "bg-blue-500/20 text-blue-300"
                      }`}
                    >
                      {t.tier.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-1.5 px-2 text-neutral-200 font-medium">
                    {t.model_name}
                  </td>
                  <td className="py-1.5 px-2 text-right font-mono">
                    {t.tokens.total_tokens}
                  </td>
                  <td className="py-1.5 px-2 text-right font-mono text-emerald-400 font-bold">
                    ${t.cost_usd.toFixed(6)}
                  </td>
                  <td className="py-1.5 px-2 text-right text-neutral-500 font-mono">
                    {t.latency_ms}ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
