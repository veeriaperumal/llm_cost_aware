# Cost-Aware Multi-Tier Cascading LLM Router

A cost-aware LLM routing engine that optimizes AI inference budgets by cascading queries through fast, cheap models first — escalating to frontier models only when confidence is low or quality demands it. Built on LangGraph with PostgreSQL-backed state, Pareto-optimal model selection, hybrid quality evaluation, and a full cost audit ledger.

---

## Architecture

```
User Prompt
    │
    ▼
┌─────────────────────────┐
│  classify_task          │  Analyze prompt complexity & task type
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  select_models          │  Query DB, run Pareto filtering, pick best model
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  execute_tier1          │  Call fast/cheap model, extract confidence score
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  decide_escalation      │  Compare confidence vs threshold
└─────┬──────────┬────────┘
      │          │
  [escalated]  [direct]
      │          │
      ▼          │
┌─────────────┐  │
│ execute_    │  │
│ tier2       │  │
└─────┬───────┘  │
      │          │
      └────┬─────┘
           ▼
┌─────────────────────────┐
│  evaluate_quality       │  Hybrid scoring (deterministic + LLM judge)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  recover_quality        │  Auto-revise if quality too low; escalate if needed
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  compute_costs          │  Full cost breakdown + spend justification
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  finalize               │  Assemble response, persist audit history
└─────────────────────────┘
```

---

## Core Features

- **Multi-tier cascading** — Queries hit cheap Tier 1 models first; escalate to expensive Tier 2 only when confidence falls below threshold
- **Pareto-optimal model selection** — Filters dominated models on quality/latency/cost axes, ranks via weighted composite score (0.45 quality, 0.30 latency, 0.25 cost)
- **Hybrid quality evaluation** — Deterministic scoring (format validity, token overlap, field matching) combined with LLM-as-judge (relevance, accuracy, faithfulness)
- **Quality recovery** — Auto-revision when quality scores fall between 0.80-0.90; escalation to frontier model when below 0.80
- **Cost audit ledger** — Every query records per-tier spend, savings vs Sonnet-only baseline, and human-readable spend justification
- **6 LLM providers** — Gemini, Groq, Mistral, Anthropic, OpenAI, and Mock (simulated) with free-tier support
- **Encrypted API key storage** — Per-user Fernet-encrypted keys stored in PostgreSQL
- **12 escalation reasons** — Machine-readable reasons for every escalation (low confidence, low quality, timeout, rate limit, provider error, etc.)

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **PostgreSQL** (required — the app needs a running instance)

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env: set DATABASE_URL and at least one API key (or keep mock mode)

# Start server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: `http://127.0.0.1:8000/docs`

### 2. Frontend

```bash
cd frontend

npm install
npm run dev
```

Dashboard: `http://localhost:3000`

### 3. One-Click Launch (Windows)

```bash
start_dev.bat
```

Opens two terminals — backend on `:8000`, frontend on `:3000`.

---

## Environment Variables

All variables are configured in `backend/.env`. Copy `.env.example` to get started.

### Server

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Backend bind address |
| `PORT` | `8000` | Backend port |

### Database

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | *(required)* | PostgreSQL connection string. Format: `postgresql+asyncpg://user:pass@host:5432/cost_aware` |

### Provider API Keys

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_PROVIDER` | *(auto-detect)* | Active provider: `gemini`, `groq`, `mistral`, `anthropic`, `openai`, or `mock` |
| `GEMINI_API_KEY` | `""` | Google Gemini API key ([get key](https://aistudio.google.com/app/apikey)) |
| `GROQ_API_KEY` | `""` | Groq LPU API key ([get key](https://console.groq.com/keys)) |
| `MISTRAL_API_KEY` | `""` | Mistral AI API key ([get key](https://console.mistral.ai/)) |
| `ANTHROPIC_API_KEY` | `""` | Anthropic Claude API key ([get key](https://console.anthropic.com/)) |
| `OPENAI_API_KEY` | `""` | OpenAI API key ([get key](https://platform.openai.com/api-keys)) |

### Routing

| Variable | Default | Description |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | `0.75` | Tier 1-to-2 escalation gate (0.0 to 1.0) |
| `PARETO_QUALITY_WEIGHT` | `0.45` | Pareto scoring: quality dimension weight |
| `PARETO_LATENCY_WEIGHT` | `0.30` | Pareto scoring: latency dimension weight |
| `PARETO_COST_WEIGHT` | `0.25` | Pareto scoring: cost dimension weight |

### Quality Evaluation

| Variable | Default | Description |
|---|---|---|
| `QUALITY_EVALUATION_ENABLED` | `true` | Toggle hybrid quality evaluation on/off |
| `JUDGE_MODEL_PROVIDER` | `anthropic` | Provider for the LLM judge used in quality scoring |
| `JUDGE_MODEL_NAME` | `claude-3-5-haiku-20241022` | Model used as the LLM judge |

### Quality Recovery

| Variable | Default | Description |
|---|---|---|
| `QUALITY_RECOVERY_ENABLED` | `true` | Toggle quality recovery (revise/escalate) on/off |
| `QUALITY_ACCEPT_THRESHOLD` | `0.90` | Quality score >= this: accept as-is |
| `QUALITY_REVISE_THRESHOLD` | `0.80` | Quality score >= this but < accept: attempt one revision |
| `QUALITY_REVISION_MODEL` | `""` | Dedicated revision model (empty = reuse current model) |
| `QUALITY_MAX_REVISIONS` | `1` | Maximum revision attempts before escalating |

### Security

| Variable | Default | Description |
|---|---|---|
| `ENCRYPTION_SECRET_KEY` | `""` | Fernet key for encrypting stored API keys |

---

## Database Schema

Five tables in PostgreSQL (auto-created on first run):

| Table | Purpose |
|---|---|
| `models` | LLM model registry — 20 models across 6 providers with capabilities and quality scores |
| `model_pricing` | Versioned pricing per model (input/output cost per million tokens, effective dates) |
| `model_quality_evaluations` | Quality evaluation records per query (task type, scores, metrics) |
| `model_quality_recoveries` | Quality recovery action log (revision attempts, escalation outcomes) |
| `user_api_keys` | Per-user Fernet-encrypted API key store |

---

## Providers

| Provider | Free Tier | Tier 1 (Fast/Cheap) | Tier 2 (Frontier) |
|---|---|---|---|
| **Google Gemini** | Yes | Gemini 2.5 Flash | Gemini 2.5 Flash Deep Synthesis |
| **Groq** | Yes | Llama 3.1 8B Instant, Qwen 3.8, GPT-OSS 120B | Llama 3.3 70B, Qwen Frontier, GPT-OSS 120B Frontier |
| **Mistral AI** | Yes | Mistral Small | Mistral Large |
| **Anthropic** | No (paid) | Claude 3.5 Haiku ($0.80/$4.00 per 1M) | Claude 3.5 Sonnet ($3.00/$15.00 per 1M) |
| **OpenAI** | No (paid) | GPT-4o-mini ($0.15/$0.60 per 1M) | GPT-4o ($2.50/$10.00 per 1M) |
| **Mock** | Yes (zero-cost) | Simulated Haiku | Simulated Sonnet |

---

## Testing

```bash
python -m pytest backend/tests -v
```

---

## API Documentation

Interactive Swagger docs available at `http://127.0.0.1:8000/docs` when the backend is running.
