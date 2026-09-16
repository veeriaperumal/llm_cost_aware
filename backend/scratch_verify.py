import httpx
import sys

base_url = "http://127.0.0.1:8000/api"
headers = {"X-User-ID": "default_user"}

print("=== 1. Root & Health Check ===")
r_root = httpx.get("http://127.0.0.1:8000/")
print("Root status:", r_root.status_code, r_root.json().get("status"))

print("\n=== 2. Models Endpoint ===")
r_models = httpx.get(f"{base_url}/models", headers=headers)
models = r_models.json()
print("Models status:", r_models.status_code, "| Total models:", len(models))
for m in models[:4]:
    print(" -", m.get("display_name"), f"({m.get('provider_name')})", "| Tier:", m.get("tier"), "| Quality:", m.get("base_quality_score"))

print("\n=== 3. Saved Keys Endpoint ===")
r_keys = httpx.get(f"{base_url}/keys", headers=headers)
keys = r_keys.json()
print("Keys status:", r_keys.status_code, "| Saved keys count:", len(keys))
for k in keys:
    print(" - Provider:", k.get("provider_name"), "| Hint:", k.get("key_hint"), "| Valid:", k.get("is_valid"))

print("\n=== 4. Chat Cascading Inference (Direct Tier 1) ===")
r_chat1 = httpx.post(f"{base_url}/chat", headers=headers, json={
    "prompt": "What is the speed of light in vacuum?",
    "provider": "auto"
}, timeout=30.0)
c1 = r_chat1.json()
print("Chat 1 Status:", r_chat1.status_code)
print("Served By:", c1.get("served_by_model"), f"({c1.get('served_by_tier')})", "| Confidence:", c1.get("confidence"), "| Escalated:", c1.get("escalation", {}).get("escalated"))
print("Cost USD:", c1.get("cost_breakdown", {}).get("total_cost_usd"))
print("Answer Preview:", c1.get("final_answer", "")[:120], "...")

print("\n=== 5. Chat Cascading Inference (Escalation to Tier 2) ===")
r_chat2 = httpx.post(f"{base_url}/chat", headers=headers, json={
    "prompt": "Design a high-throughput event sourcing architecture using Kafka and CQRS with consistency proofs.",
    "provider": "gemini"
}, timeout=30.0)
c2 = r_chat2.json()
print("Chat 2 Status:", r_chat2.status_code)
print("Served By:", c2.get("served_by_model"), f"({c2.get('served_by_tier')})", "| Confidence:", c2.get("confidence"), "| Escalated:", c2.get("escalation", {}).get("escalated"))
print("Cost USD:", c2.get("cost_breakdown", {}).get("total_cost_usd"))
print("Answer Preview:", c2.get("final_answer", "")[:120], "...")

print("\n=== 6. History & Analytics Endpoints ===")
r_hist = httpx.get(f"{base_url}/history")
r_analytics = httpx.get(f"{base_url}/analytics")
print("History items logged:", len(r_hist.json()))
print("Total Queries in Analytics:", r_analytics.json().get("total_queries"))
print("Total Spend: $", r_analytics.json().get("total_spend_usd"))
print("Total Savings: $", r_analytics.json().get("total_savings_usd"))
print("Escalation Rate: %", r_analytics.json().get("escalation_rate_percent"))
