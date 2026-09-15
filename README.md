# Cost-Aware Cascading LLM Router & Escalation System

A production-grade, cost-aware LLM routing engine that optimizes AI inference budgets by implementing dynamic multi-tier confidence gates, automatic frontier escalation, and spend audit ledgers.

---

## 🏗️ Architectural Workflow

When a user submits a prompt, the query cascades through the following multi-tier evaluation pipeline:

```
User Prompt
    │
    ▼
Tier 1: Fast & Cost-Efficient Model (e.g., Claude 3.5 Haiku / Gemini 1.5 Flash / Llama 3.1 8B)
    │
    ├── Evaluates response & structured self-confidence score (e.g. confidence = 0.61)
    │
    ▼
Confidence Decision Gate (Threshold = 0.75)
    │
    ├── If confidence >= 0.75  ──►  Direct Return: Answer served at 1/10th the cost (100% Sonnet budget saved)
    │
    └── If confidence < 0.75   ──►  ESCALATE (reason = "low_confidence")
                                        │
                                        ▼
                                    Tier 2: Frontier Intelligence Model (Claude 3.5 Sonnet / Gemini 1.5 Pro / Llama 3.3 70B)
                                        │
                                        ▼
                                    Synthesizes Final Authoritative Answer
                                        │
                                        ▼
                                    Audit Ledger records why we spent the extra money
```

---

## 🔑 Free Tier API Keys vs Commercial API Keys Review

| Provider | Free Tier Available? | Recommended Models | Notes & Pricing Rate |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | **YES (Free Tier)** | • Tier 1: `gemini-1.5-flash`<br>• Tier 2: `gemini-1.5-pro` | Free tier available on [Google AI Studio](https://aistudio.google.com/app/apikey). High rate limits (15 RPM) for zero-cost live testing. |
| **Groq Cloud** | **YES (Free Tier)** | • Tier 1: `llama-3.1-8b-instant`<br>• Tier 2: `llama-3.3-70b-versatile` | Ultra-fast LPU inference available for free at [Groq Console](https://console.groq.com/keys). |
| **Mistral AI** | **YES (Free Trial)** | • Tier 1: `mistral-small`<br>• Tier 2: `mistral-large` | Free experimentation credits on [La Plateforme](https://console.mistral.ai/). |
| **Anthropic (Claude)** | **NO (Paid Only)** | • Tier 1: `claude-3-5-haiku`<br>• Tier 2: `claude-3-5-sonnet` | Requires minimum $5 prepaid balance on [Anthropic Console](https://console.anthropic.com/). Haiku: $0.80/$4.00 per 1M; Sonnet: $3.00/$15.00 per 1M. |
| **OpenAI** | **NO (Paid Only)** | • Tier 1: `gpt-4o-mini`<br>• Tier 2: `gpt-4o` | Requires paid API credit tier on [OpenAI Platform](https://platform.openai.com/). Mini: $0.15/$0.60 per 1M; 4o: $2.50/$10.00 per 1M. |
| **Simulated Mode** | **YES (Zero-Cost / Offline)** | • Tier 1: Haiku (Simulated)<br>• Tier 2: Sonnet (Simulated) | Default zero-config mode that accurately demonstrates Haiku (confidence = 0.61) ➔ ESCALATE (low_confidence) ➔ Sonnet. |

---

## 🚀 Quick Start & Production Setup

### Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- **Node.js 18+** & **npm** (Tested on Node v24)

---

### Step 1: Backend Setup (FastAPI)

```bash
# Navigate to backend folder
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Configure environment variables (optional: add API keys or keep DEFAULT_PROVIDER=mock)
copy .env.example .env

# Run FastAPI Backend Server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API and Interactive Swagger documentation will be live at `http://127.0.0.1:8000/docs`.*

---

### Step 2: Frontend Setup (Next.js SaaS UI)

```bash
# In a new terminal, navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start Next.js Development Server
npm run dev
```
*Frontend SaaS Dashboard will be live at `http://localhost:3000`.*

---

## 🧪 Automated Testing

Run the test suite to verify the cascading pipeline, low-confidence escalation, threshold gates, and cost ledger calculations:

```bash
python -m pytest backend/tests -v
```

---

## 📊 Features & UI Capabilities

1. **Interactive Cascade Visualizer**: Animated pipeline tracking Tier 1 inference, confidence gauge (0.00 to 1.00), threshold edge, and escalation badges.
2. **Instant Presets**:
   - *Complicated Q&A*: Simulates complex query triggering `confidence = 0.61 < 0.75` ➔ `ESCALATE` (reason: `low_confidence`) ➔ Sonnet final answer.
   - *Simple FAQ*: Solves instantly with high confidence `0.94` at Tier 1, avoiding frontier cost.
3. **Spend Justification Ledger**: Automatically generates executive financial reasoning explaining why the extra money was (or wasn't) spent.
4. **ROI Analytics**: Real-time aggregated statistics comparing total spend vs Sonnet-only baseline cost, net savings ($ and %), and escalation frequency.
