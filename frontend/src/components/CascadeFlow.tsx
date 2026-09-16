"use client";

import React from "react";
import { ChatResponse, EscalationReason, ESCALATION_LABELS, ESCALATION_COLORS } from "../types";
import {
  ArrowDown,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  ShieldAlert,
  Cpu,
} from "lucide-react";

interface CascadeFlowProps {
  response: ChatResponse | null;
  isLoading: boolean;
  threshold: number;
}

export const CascadeFlow: React.FC<CascadeFlowProps> = ({
  response,
  isLoading,
  threshold,
}) => {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-neutral-700 bg-[#2f2f2f] p-4 text-center">
        <div className="flex flex-col items-center space-y-3 py-4">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-neutral-300 text-sm">Executing Cascade Pipeline...</div>
        </div>
      </div>
    );
  }

  if (!response) {
    return (
      <div className="rounded-xl border border-neutral-700 bg-[#2f2f2f] p-4 text-center">
        <div className="py-6">
          <Cpu className="w-6 h-6 text-blue-400 mx-auto mb-2" />
          <p className="text-xs text-neutral-400">
            Pipeline Ready (Threshold: {threshold.toFixed(2)})
          </p>
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
    <div className="rounded-xl border border-neutral-700 bg-[#2f2f2f] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-700">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-neutral-200">
            Cascade Flow
          </span>
          <span className="text-[10px] text-neutral-500 font-mono">
            {response.total_latency_ms}ms
          </span>
        </div>
        <span
          className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
            isEscalated
              ? "bg-amber-500/20 text-amber-300"
              : "bg-emerald-500/20 text-emerald-300"
          }`}
        >
          {isEscalated ? "ESCALATED" : "TIER 1 DIRECT"}
        </span>
      </div>

      {/* Flow Steps */}
      <div className="p-4 space-y-3">
        {/* User Query */}
        <div className="flex items-center gap-2 text-xs">
          <span className="w-5 h-5 rounded bg-neutral-700 flex items-center justify-center text-[10px]">
            👤
          </span>
          <span className="text-neutral-400">Query:</span>
          <span className="text-neutral-200 truncate flex-1">
            &quot;{response.prompt}&quot;
          </span>
        </div>

        <ArrowDown className="w-3 h-3 text-neutral-600 ml-2" />

        {/* Tier 1 */}
        <div
          className={`p-3 rounded-lg border ${
            isHighConfidence
              ? "bg-emerald-950/30 border-emerald-500/30"
              : "bg-neutral-800 border-neutral-700"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-cyan-500/20 text-cyan-300">
                TIER 1
              </span>
              <span className="text-xs font-medium text-neutral-200">
                {tier1Trace?.model_name || "Haiku"}
              </span>
            </div>
            <span className="text-[10px] font-mono text-neutral-400">
              ${tier1Trace?.cost_usd.toFixed(6)}
            </span>
          </div>

          {/* Confidence bar */}
          <div className="flex items-center gap-2 text-[10px]">
            <span className="text-neutral-500">Confidence:</span>
            <div className="flex-1 bg-neutral-700 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isHighConfidence
                    ? "bg-emerald-500"
                    : "bg-gradient-to-r from-rose-500 to-amber-500"
                }`}
                style={{ width: `${Math.min(100, Math.max(5, confidence * 100))}%` }}
              />
            </div>
            <span
              className={`font-mono font-bold ${
                isHighConfidence ? "text-emerald-400" : "text-amber-400"
              }`}
            >
              {confidence.toFixed(2)}
            </span>
          </div>

          {/* Uncertainty reasons */}
          {tier1Trace?.uncertainty_reasons &&
            tier1Trace.uncertainty_reasons.length > 0 && (
              <div className="mt-2 text-[10px] text-amber-300/90 bg-amber-500/10 p-2 rounded border border-amber-500/20">
                <AlertTriangle className="w-3 h-3 inline mr-1" />
                {tier1Trace.uncertainty_reasons.join("; ")}
              </div>
            )}
        </div>

        {/* Escalation gate */}
        {isEscalated ? (
          <>
            <ArrowDown className="w-3 h-3 text-amber-400 ml-2 animate-bounce" />
            <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-500/30">
              <div className="flex items-center gap-1.5 mb-1">
                <ShieldAlert className="w-3 h-3 text-amber-400" />
                <span className="text-[10px] font-bold text-amber-400 uppercase">
                  Escalate Gate
                </span>
                {response.escalation.reason && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded border font-bold ${
                      ESCALATION_COLORS[(response.escalation.reason as EscalationReason)] ||
                      "bg-neutral-500/20 text-neutral-300 border-neutral-500/30"
                    }`}
                  >
                    {ESCALATION_LABELS[(response.escalation.reason as EscalationReason)] ||
                      response.escalation.reason}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-neutral-400">
                {response.escalation.explanation ||
                  `Confidence ${confidence.toFixed(2)} < threshold ${threshold.toFixed(2)}`}
              </p>
            </div>
            <ArrowDown className="w-3 h-3 text-neutral-600 ml-2" />
            <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-blue-500/20 text-blue-300">
                    TIER 2
                  </span>
                  <span className="text-xs font-medium text-neutral-200">
                    {tier2Trace?.model_name || "Sonnet"}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-blue-300">
                  ${tier2Trace?.cost_usd.toFixed(6)}
                </span>
              </div>
            </div>
          </>
        ) : (
          <>
            <ArrowDown className="w-3 h-3 text-emerald-400 ml-2" />
            <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-medium text-neutral-200">
                  Sufficient confidence ({confidence.toFixed(2)} &ge;{" "}
                  {threshold.toFixed(2)})
                </span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                100% SAVED
              </span>
            </div>
          </>
        )}

        {/* Spend justification */}
        <div className="flex items-start gap-2 text-[11px] text-neutral-400 pt-1">
          <DollarSign className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
          <span>{response.cost_breakdown.spend_justification}</span>
        </div>
      </div>
    </div>
  );
};
