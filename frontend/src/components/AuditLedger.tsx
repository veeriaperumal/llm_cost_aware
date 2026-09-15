"use client";

import React, { useEffect, useState } from "react";
import { QueryHistoryItem, AnalyticsSummary } from "../types";
import { Activity, DollarSign, TrendingDown, Layers, ShieldAlert, CheckCircle2, RefreshCw } from "lucide-react";

interface AuditLedgerProps {
  history: QueryHistoryItem[];
  analytics: AnalyticsSummary | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const AuditLedger: React.FC<AuditLedgerProps> = ({ history, analytics, onRefresh, isLoading }) => {
  return (
    <div className="space-y-6">
      {/* Analytics KPI Summary Row */}
      {analytics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass-panel p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Total Queries</span>
              <Activity className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-black text-white font-mono">{analytics.total_queries}</div>
            <div className="text-[11px] text-slate-400 mt-1">
              {analytics.tier1_handled_count} Tier-1 only / {analytics.tier2_escalated_count} Escalated
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Total Spend</span>
              <DollarSign className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-black text-amber-300 font-mono">
              ${analytics.total_spend_usd.toFixed(4)}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Baseline: ${analytics.total_baseline_cost_usd.toFixed(4)}
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Net ROI Savings</span>
              <TrendingDown className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400 font-mono">
              ${analytics.total_savings_usd.toFixed(4)}
            </div>
            <div className="text-[11px] text-emerald-300 font-semibold mt-1">
              +{analytics.average_savings_percent}% budget saved
            </div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Escalation Rate</span>
              <ShieldAlert className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-black text-purple-300 font-mono">
              {analytics.escalation_rate_percent}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Triggered on low confidence
            </div>
          </div>
        </div>
      )}

      {/* Escalation Reasons Breakdown Card */}
      {analytics && Object.keys(analytics.escalation_reasons_breakdown).length > 0 && (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
            Escalation Reason Distribution (Why extra money was spent)
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(analytics.escalation_reasons_breakdown).map(([reason, count]) => (
              <div
                key={reason}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs"
              >
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span className="font-mono text-slate-200">reason = "{reason}"</span>
                <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold font-mono text-[10px]">
                  {count} {count === 1 ? "time" : "times"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Query Audit History Table */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Historical Execution & Cost Audit Ledger</h3>
            <p className="text-[11px] text-slate-400">Chronological trace of prompts, confidence levels, escalation triggers, and recorded spend justification.</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                if (confirm("Are you sure you want to clear all audit records?")) {
                  await fetch("/api/history", { method: "DELETE" });
                  onRefresh();
                }
              }}
              className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-xs text-rose-300 transition"
            >
              Clear Audit Data
            </button>
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:text-white transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500">
            No queries logged yet. Submit prompts in the playground to populate the audit ledger!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="py-2.5 px-3 font-semibold">Timestamp</th>
                  <th className="py-2.5 px-3 font-semibold">Prompt</th>
                  <th className="py-2.5 px-3 font-semibold">Confidence</th>
                  <th className="py-2.5 px-3 font-semibold">Routing Status</th>
                  <th className="py-2.5 px-3 font-semibold">Model Served</th>
                  <th className="py-2.5 px-3 font-semibold">Cost Incurred</th>
                  <th className="py-2.5 px-3 font-semibold">Spend Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans text-[11px]">
                {history.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3 text-slate-400 font-mono text-[10px] whitespace-nowrap">
                      {item.timestamp}
                    </td>
                    <td className="py-3 px-3 text-slate-200 font-medium max-w-xs truncate" title={item.prompt}>
                      {item.prompt}
                    </td>
                    <td className="py-3 px-3 font-mono font-bold">
                      <span
                        className={
                          item.confidence >= 0.75 ? "text-emerald-400" : "text-amber-400"
                        }
                      >
                        {item.confidence.toFixed(2)}
                      </span>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      {item.escalated ? (
                        <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold text-[10px] border border-amber-500/30">
                          Escalated ({item.escalation_reason})
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold text-[10px] border border-emerald-500/30">
                          Tier 1 Direct
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300 font-medium whitespace-nowrap">
                      {item.served_by_model}
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-amber-300 whitespace-nowrap">
                      ${item.total_cost_usd.toFixed(6)}
                    </td>
                    <td className="py-3 px-3 text-slate-400 max-w-md truncate" title={item.spend_justification}>
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
