"use client";

import React from "react";
import { QueryHistoryItem, AnalyticsSummary } from "../types";
import {
  Activity,
  DollarSign,
  TrendingDown,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";

interface AuditLedgerProps {
  history: QueryHistoryItem[];
  analytics: AnalyticsSummary | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const AuditLedger: React.FC<AuditLedgerProps> = ({
  history,
  analytics,
  onRefresh,
  isLoading,
}) => {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* KPI Cards */}
      {analytics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl border border-neutral-700 bg-[#2f2f2f]">
            <div className="flex items-center justify-between text-neutral-500 text-[10px] font-medium uppercase mb-2">
              <span>Total Queries</span>
              <Activity className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <div className="text-xl font-bold text-white font-mono">
              {analytics.total_queries}
            </div>
            <div className="text-[10px] text-neutral-500 mt-1">
              {analytics.tier1_handled_count} Tier-1 / {analytics.tier2_escalated_count} Escalated
            </div>
          </div>

          <div className="p-4 rounded-xl border border-neutral-700 bg-[#2f2f2f]">
            <div className="flex items-center justify-between text-neutral-500 text-[10px] font-medium uppercase mb-2">
              <span>Total Spend</span>
              <DollarSign className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-xl font-bold text-amber-300 font-mono">
              ${analytics.total_spend_usd.toFixed(4)}
            </div>
            <div className="text-[10px] text-neutral-500 mt-1">
              Baseline: ${analytics.total_baseline_cost_usd.toFixed(4)}
            </div>
          </div>

          <div className="p-4 rounded-xl border border-neutral-700 bg-[#2f2f2f]">
            <div className="flex items-center justify-between text-neutral-500 text-[10px] font-medium uppercase mb-2">
              <span>Net Savings</span>
              <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-xl font-bold text-emerald-400 font-mono">
              ${analytics.total_savings_usd.toFixed(4)}
            </div>
            <div className="text-[10px] text-emerald-300 font-medium mt-1">
              +{analytics.average_savings_percent}% saved
            </div>
          </div>

          <div className="p-4 rounded-xl border border-neutral-700 bg-[#2f2f2f]">
            <div className="flex items-center justify-between text-neutral-500 text-[10px] font-medium uppercase mb-2">
              <span>Escalation Rate</span>
              <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <div className="text-xl font-bold text-purple-300 font-mono">
              {analytics.escalation_rate_percent}%
            </div>
            <div className="text-[10px] text-neutral-500 mt-1">
              Triggered on low confidence
            </div>
          </div>
        </div>
      )}

      {/* Escalation Reasons */}
      {analytics &&
        Object.keys(analytics.escalation_reasons_breakdown).length > 0 && (
          <div className="p-4 rounded-xl border border-neutral-700 bg-[#2f2f2f]">
            <h4 className="text-[10px] font-medium uppercase text-neutral-500 mb-3">
              Escalation Reasons
            </h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(analytics.escalation_reasons_breakdown).map(
                ([reason, count]) => (
                  <div
                    key={reason}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-[11px]"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    <span className="text-neutral-300 font-mono">{reason}</span>
                    <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold text-[10px]">
                      {count}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>
        )}

      {/* History Table */}
      <div className="rounded-xl border border-neutral-700 bg-[#2f2f2f] overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700">
          <h3 className="text-xs font-semibold text-neutral-200">
            Audit Ledger
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                if (confirm("Clear all audit records?")) {
                  await fetch("/api/history", { method: "DELETE" });
                  onRefresh();
                }
              }}
              className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-[10px] text-rose-300 transition"
            >
              Clear
            </button>
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-[10px] text-neutral-300 transition disabled:opacity-50"
            >
              <RefreshCw
                className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </button>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="py-12 text-center text-xs text-neutral-500">
            No queries logged yet. Submit prompts in the playground!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[11px]">
              <thead>
                <tr className="border-b border-neutral-700 text-neutral-500">
                  <th className="py-2 px-3 font-medium">Time</th>
                  <th className="py-2 px-3 font-medium">Prompt</th>
                  <th className="py-2 px-3 font-medium">Confidence</th>
                  <th className="py-2 px-3 font-medium">Status</th>
                  <th className="py-2 px-3 font-medium">Model</th>
                  <th className="py-2 px-3 font-medium">Cost</th>
                  <th className="py-2 px-3 font-medium hidden lg:table-cell">
                    Rationale
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-700/50">
                {history.map((item) => (
                  <tr key={item.id} className="text-neutral-300 hover:bg-neutral-800/30">
                    <td className="py-2 px-3 text-neutral-500 font-mono text-[10px] whitespace-nowrap">
                      {item.timestamp}
                    </td>
                    <td className="py-2 px-3 max-w-[200px] truncate" title={item.prompt}>
                      {item.prompt}
                    </td>
                    <td className="py-2 px-3 font-mono font-bold">
                      <span
                        className={
                          item.confidence >= 0.75
                            ? "text-emerald-400"
                            : "text-amber-400"
                        }
                      >
                        {item.confidence.toFixed(2)}
                      </span>
                    </td>
                    <td className="py-2 px-3 whitespace-nowrap">
                      {item.escalated ? (
                        <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-medium text-[10px]">
                          Escalated
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-medium text-[10px]">
                          Tier 1
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3 whitespace-nowrap text-neutral-400">
                      {item.served_by_model}
                    </td>
                    <td className="py-2 px-3 font-mono font-bold text-amber-300 whitespace-nowrap">
                      ${item.total_cost_usd.toFixed(6)}
                    </td>
                    <td className="py-2 px-3 text-neutral-500 max-w-[200px] truncate hidden lg:table-cell" title={item.spend_justification}>
                      {item.spend_justification}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
