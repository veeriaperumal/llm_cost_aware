import json
import os
from typing import List, Dict, Any, Optional
from app.models.schemas import QueryHistoryItem, AnalyticsSummary

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "query_history.json")

class HistoryStore:
    def __init__(self):
        self._history: List[QueryHistoryItem] = []
        self._load()

    def _load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._history = [QueryHistoryItem(**item) for item in data]
            except Exception:
                self._history = []

    def _save(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self._history], f, indent=2)
        except Exception:
            pass

    def add(self, item: QueryHistoryItem):
        self._history.insert(0, item)  # Latest first
        # Keep last 100 entries
        if len(self._history) > 100:
            self._history = self._history[:100]
        self._save()

    def clear(self):
        self._history = []
        self._save()

    def get_all(self) -> List[QueryHistoryItem]:
        return self._history

    def get_analytics(self) -> AnalyticsSummary:
        if not self._history:
            return AnalyticsSummary()

        total_queries = len(self._history)
        total_spend = sum(item.total_cost_usd for item in self._history)
        total_savings = sum(item.savings_usd for item in self._history)
        escalated_items = [item for item in self._history if item.escalated]
        escalated_count = len(escalated_items)
        tier1_count = total_queries - escalated_count
        
        reasons_breakdown: Dict[str, int] = {}
        for item in escalated_items:
            reason = item.escalation_reason or "unknown"
            reasons_breakdown[reason] = reasons_breakdown.get(reason, 0) + 1

        total_baseline = total_spend + total_savings
        avg_savings_pct = round((total_savings / total_baseline * 100.0) if total_baseline > 0 else 0.0, 2)
        escalation_rate = round((escalated_count / total_queries * 100.0) if total_queries > 0 else 0.0, 2)

        return AnalyticsSummary(
            total_queries=total_queries,
            total_spend_usd=round(total_spend, 6),
            total_baseline_cost_usd=round(total_baseline, 6),
            total_savings_usd=round(total_savings, 6),
            average_savings_percent=avg_savings_pct,
            escalation_rate_percent=escalation_rate,
            tier1_handled_count=tier1_count,
            tier2_escalated_count=escalated_count,
            escalation_reasons_breakdown=reasons_breakdown
        )

history_store = HistoryStore()
