# Cost-Aware Multi-Tier Cascading LLM Router

> **Production-grade, cost-aware LLM routing engine that optimizes AI inference budgets through dynamic multi-tier confidence gates, Pareto-optimal model selection, hybrid quality evaluation, and full cost audit ledgers.**

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What it does ?

**Cost-Aware Multi-Tier Cascading LLM Router** is a production-grade LLM routing system that ensures every query is served by the cheapest capable model — escalating to expensive frontier models only when confidence is low or quality demands it.

1. **Classify & Select**: Analyzes prompt complexity, task type, and tool requirements. Queries the model registry (20 models across 6 providers), runs Pareto filtering on quality/latency/cost axes, and selects the optimal Tier 1 model.
2. **Tier 1 Execution (Fast & Cheap)**: Sends the prompt to a cost-efficient model (e.g., Gemini Flash, Llama 3.1 8B, GPT-4o-mini). The model returns a response with a structured self-confidence score (0.0–1.0) and uncertainty reasons.
3. **Confidence Decision Gate**: Compares the confidence score against a configurable threshold (default 0.75). If below threshold, the query escalates to a Tier 2 frontier model with a machine-readable reason (`LOW_CONFIDENCE`).
4. **Tier 2 Execution (Frontier)**: If escalated, a powerful model (e.g., Claude 3.5 Sonnet, Llama 3.3 70B, GPT-4o) synthesizes an authoritative answer using the full escalation context — original prompt, Tier 1 draft, uncertainty reasons.
5. **Hybrid Quality Evaluation**: Every response is scored by a hybrid evaluator combining deterministic rules (format validity, token overlap, field matching) with an LLM judge (relevance, accuracy, faithfulness).
6. **Quality Recovery**: If quality scores fall between 0.80–0.90, the system auto-revises once. If below 0.80, it escalates to a stronger model. Tier 2 responses that still score low are accepted as the best available.
7. **Cost Audit Ledger**: Every query records per-tier spend, savings vs Sonnet-only baseline, escalation rationale, and a human-readable spend justification explaining why the extra money was (or wasn't) spent.

---

## Problem Statement

Most LLM-powered applications waste money on every query:

- **One-Size-Fits-All Models**: Simple FAQ queries get routed to expensive frontier models like GPT-4o or Claude Sonnet, burning through API budgets at 10x the necessary cost.
- **No Confidence Gating**: Applications lack the ability to detect when a cheap model is uncertain and only escalate when truly needed.
- **No Quality Feedback Loop**: Once a model responds, there's no mechanism to verify the response is actually good enough — bad answers slip through silently.
- **Opaque Spend Justification**: Teams can't explain *why* a particular model was chosen or why escalation was triggered, making cost optimization impossible.
- **Static Model Selection**: Choosing one model for all queries ignores the Pareto trade-offs between quality, latency, and cost that different providers offer.

---

## Solution

**Cost-Aware Cascading LLM Router** eliminates wasted spend by routing every query through a multi-tier pipeline that only escalates when quality demands it:

- **Confidence-Gated Cascading**: Tier 1 handles ~70% of queries at 1/10th the cost. Only genuinely uncertain responses escalate to Tier 2, with every escalation justified by a machine-readable reason.
- **Pareto-Optimal Selection**: Instead of picking a single model, the system evaluates all available models on quality, latency, and cost — filtering dominated options and selecting the best non-dominated candidate via weighted scoring.
- **Hybrid Quality Evaluation**: Deterministic checks (format validity, field matching, token overlap) catch structural failures instantly. LLM judge scoring (relevance, accuracy, faithfulness) catches semantic failures.
- **Auto-Recovery**: Responses in the marginal quality zone (0.80–0.90) get one revision attempt. Below 0.80, the system escalates to a frontier model automatically.
- **Full Cost Transparency**: Every response includes a complete audit trail — which model served it, why it was selected, what the spend was, and how much was saved vs a naive all-frontier approach.

---

## How to Run it

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **PostgreSQL** running instance

---

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd cost_aware
```

---

### Step 2: Backend Setup & Execution
```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
```

*Fill in your keys in `backend/.env` (see the Environment Variables section below).*

```bash
# Start the FastAPI Backend Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs locally at: `http://127.0.0.1:8000` (Swagger documentation at `http://127.0.0.1:8000/docs`)*

---

### Step 3: Frontend Setup & Execution
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Next.js Development Server
npm run dev
```
*Frontend runs locally at: `http://localhost:3000`*

---

### Step 4: One-Click Launch (Windows)
```bash
start_dev.bat
```
Opens two terminals — backend on `:8000`, frontend on `:3000`.

---

## What the ENV variables

Create your `.env` file in the `backend/` directory (copy from `.env.example`).

### 1. Server & Database

```env
# ==========================================
# Server Configuration
# ==========================================
HOST=127.0.0.1
PORT=8000

# ==========================================
# Database (PostgreSQL required)
# ==========================================
# Format: postgresql+asyncpg://user:password@host:5432/cost_aware
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cost_aware
```

---

### 2. Provider API Keys

```env
# ==========================================
# Default Provider (leave empty for auto-detect)
# Options: gemini, groq, mistral, anthropic, openai, mock
# ==========================================
DEFAULT_PROVIDER=mock

# ==========================================
# Provider API Keys (configure at least one for live mode)
# ==========================================

# Google Gemini (Free Tier) - https://aistudio.google.com/app/apikey
GEMINI_API_KEY=

# Groq (Free Tier) - https://console.groq.com/keys
GROQ_API_KEY=

# Mistral AI (Free Tier) - https://console.mistral.ai/
MISTRAL_API_KEY=

# Anthropic Claude (Paid) - https://console.anthropic.com/
ANTHROPIC_API_KEY=

# OpenAI (Paid) - https://platform.openai.com/api-keys
OPENAI_API_KEY=
```

---

### 3. Routing & Pareto Selection

```env
# ==========================================
# Confidence Gate
# ==========================================
# Threshold for Tier 1 -> Tier 2 escalation (0.0 to 1.0)
CONFIDENCE_THRESHOLD=0.75

# ==========================================
# Pareto-Optimal Model Selection Weights (must sum to 1.0)
# ==========================================
PARETO_QUALITY_WEIGHT=0.45
PARETO_LATENCY_WEIGHT=0.30
PARETO_COST_WEIGHT=0.25
```

---

### 4. Quality Evaluation

```env
# ==========================================
# Quality Evaluation (hybrid: deterministic + LLM judge)
# ==========================================
QUALITY_EVALUATION_ENABLED=true

# LLM Judge used for quality scoring
JUDGE_MODEL_PROVIDER=anthropic
JUDGE_MODEL_NAME=claude-3-5-haiku-20241022
```

---

### 5. Quality Recovery

```env
# ==========================================
# Quality Recovery (revise / escalate when quality is low)
# ==========================================
QUALITY_RECOVERY_ENABLED=true

# Score >= 0.90: accept as-is
QUALITY_ACCEPT_THRESHOLD=0.90

# Score >= 0.80 but < 0.90: attempt one revision
QUALITY_REVISE_THRESHOLD=0.80

# Dedicated revision model (empty = reuse current model)
QUALITY_REVISION_MODEL=

# Maximum revision attempts before escalating
QUALITY_MAX_REVISIONS=1
```

---

### 6. Security

```env
# ==========================================
# Fernet Encryption Key for API Key Storage
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# ==========================================
ENCRYPTION_SECRET_KEY=
```

---

## Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Browser)"]
        UI["Next.js 16 Web Application<br/>(Tailwind CSS 4 + React 19)"]
    end

    subgraph BackendEngine ["FastAPI Backend Engine"]
        Router["FastAPI REST Router<br/>(13 API Endpoints)"]
        DB["PostgreSQL<br/>(5 Tables: models, pricing,<br/>evaluations, recoveries, keys)"]
        
        subgraph LangGraphWorkflow ["LangGraph 9-Node Pipeline"]
            C1["classify_task<br/>(complexity & task type)"]
            C2["select_models<br/>(Pareto filtering)"]
            C3["execute_tier1<br/>(fast/cheap model)"]
            C4["decide_escalation<br/>(confidence gate)"]
            C5["execute_tier2<br/>(frontier model)"]
            C6["evaluate_quality<br/>(hybrid scoring)"]
            C7["recover_quality<br/>(revise/escalate)"]
            C8["compute_costs<br/>(spend justification)"]
            C9["finalize<br/>(audit persistence)"]
        end
        
        subgraph Providers ["LLM Providers"]
            Gemini["Google Gemini"]
            Groq["Groq LPU"]
            Mistral["Mistral AI"]
            Anthropic["Anthropic Claude"]
            OpenAI["OpenAI"]
            Mock["Mock (Simulated)"]
        end
    end

    subgraph Checkpointing ["State Persistence"]
        PG["AsyncPostgresSaver<br/>(LangGraph Checkpointer)"]
    end

    UI <-->|POST /api/chat| Router
    Router <--> LangGraphWorkflow
    Router <--> DB
    LangGraphWorkflow <--> Providers
    LangGraphWorkflow <--> PG
    C1 --> C2 --> C3 --> C4
    C4 -->|escalated| C5 --> C6
    C4 -->|direct| C6
    C6 --> C7 --> C8 --> C9
```

---

## Core Features

| Feature | Description |
|---|---|
| **Multi-Tier Cascading** | Tier 1 handles ~70% of queries at 1/10th cost; only uncertain responses escalate to Tier 2 |
| **Pareto-Optimal Selection** | Filters dominated models on quality/latency/cost, ranks via weighted composite score |
| **Hybrid Quality Evaluation** | Deterministic rules + LLM judge scoring (relevance, accuracy, faithfulness) |
| **Quality Recovery** | Auto-revise (0.80–0.90) or escalate (< 0.80) when quality is insufficient |
| **Cost Audit Ledger** | Per-tier spend, savings vs baseline, human-readable spend justification |
| **6 LLM Providers** | Gemini, Groq, Mistral, Anthropic, OpenAI, Mock — with free-tier support |
| **Encrypted API Keys** | Per-user Fernet-encrypted keys stored in PostgreSQL |
| **12 Escalation Reasons** | Machine-readable reasons for every escalation (LOW_CONFIDENCE, LOW_QUALITY, MODEL_TIMEOUT, etc.) |

---

## Database Schema

| Table | Purpose |
|---|---|
| `models` | LLM model registry — 20 models across 6 providers with capabilities and quality scores |
| `model_pricing` | Versioned pricing per model (input/output cost per million tokens, effective dates) |
| `model_quality_evaluations` | Quality evaluation records per query (task type, scores, metrics) |
| `model_quality_recoveries` | Quality recovery action log (revision attempts, escalation outcomes) |
| `user_api_keys` | Per-user Fernet-encrypted API key store |

---

## API Endpoints

All endpoints are prefixed with `/api`. Interactive Swagger docs at `http://127.0.0.1:8000/docs`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Execute cascading LLM pipeline (main endpoint) |
| `GET` | `/api/models` | All registered LLM models with Pareto scores |
| `GET` | `/api/providers` | Provider catalog + key configuration status |
| `GET` | `/api/keys` | List user's saved API keys (masked) |
| `POST` | `/api/keys` | Save/update encrypted API key |
| `DELETE` | `/api/keys/{provider}` | Delete saved API key |
| `POST` | `/api/keys/validate` | Test API key against live provider |
| `GET` | `/api/history` | Query & escalation audit history |
| `DELETE` | `/api/history` | Clear audit history |
| `GET` | `/api/analytics` | Aggregate ROI metrics, savings, escalation rates |
| `GET` | `/api/quality` | Quality evaluation history |
| `GET` | `/api/quality/recovery` | Quality recovery action history |
| `GET` | `/` | Health check |

---

## Providers

| Provider | Free Tier | Tier 1 (Fast/Cheap) | Tier 2 (Frontier) |
|---|---|---|---|
| **Google Gemini** | Yes | Gemini 2.5 Flash | Gemini 2.5 Flash Deep Synthesis |
| **Groq** | Yes | Llama 3.1 8B, Qwen 3.8, GPT-OSS 120B | Llama 3.3 70B, Qwen Frontier |
| **Mistral AI** | Yes | Mistral Small | Mistral Large |
| **Anthropic** | No (paid) | Claude 3.5 Haiku ($0.80/$4.00 per 1M) | Claude 3.5 Sonnet ($3.00/$15.00 per 1M) |
| **OpenAI** | No (paid) | GPT-4o-mini ($0.15/$0.60 per 1M) | GPT-4o ($2.50/$10.00 per 1M) |
| **Mock** | Yes (zero-cost) | Simulated Haiku | Simulated Sonnet |

---

## Step by Step Implementation Journey

### Phase 1: Core Routing Engine
- Built the foundational cascading router with Tier 1/Tier 2 execution, confidence scoring, and escalation gate.
- Implemented multi-provider LLM client supporting Gemini, Groq, Mistral, Anthropic, OpenAI, and Mock simulation.
- Created cost tracking system with versioned pricing, per-query cost breakdown, and savings calculation vs Sonnet-only baseline.

### Phase 2: LangGraph Pipeline
- Migrated the linear router to a LangGraph `StateGraph` with 9 nodes: classify, select, execute_tier1, decide_escalation, execute_tier2, evaluate_quality, recover_quality, compute_costs, finalize.
- Defined `RouterState` TypedDict with 61 fields covering task classification, model selection, execution traces, quality scores, recovery actions, and cost breakdown.
- Configured PostgreSQL-backed `AsyncPostgresSaver` checkpointer for durable state with automatic fallback to in-memory `MemorySaver`.

### Phase 3: Pareto-Optimal Model Selection
- Implemented Pareto dominance filtering that removes dominated models from the quality/latency/cost trade-off space.
- Added min-max normalization across all three dimensions before weighted composite scoring.
- Built dynamic model selection per query that considers available API keys, provider preferences, and Pareto rankings.

### Phase 4: Quality Evaluation Pipeline
- Created a hybrid quality evaluator combining deterministic scoring (format validity, token overlap, JSON field matching) with LLM-as-judge evaluation (relevance, accuracy, faithfulness).
- Built a task classifier (classification, extraction, summarization, QA, tool calling) that routes to the appropriate evaluation strategy.
- Added configurable judge model selection and quality score blending (60% deterministic, 40% judge).

### Phase 5: Quality Recovery System
- Implemented the quality recovery gate that runs after evaluation: accept (>= 0.90), revise (0.80–0.90), escalate (< 0.80).
- Built auto-revision with detailed metrics feedback in the revision prompt so the model knows exactly what to improve.
- Added configurable thresholds, max revision attempts, and graceful fallback when revision or escalation fails.

### Phase 6: Escalation Reason Framework
- Defined 12 machine-readable escalation reasons in `EscalationReason` enum: LOW_CONFIDENCE, LOW_QUALITY, TOOL_FAILURE, MODEL_TIMEOUT, MODEL_RATE_LIMIT, PROVIDER_ERROR, BUDGET_POLICY, CONTEXT_LIMIT, STRUCTURED_OUTPUT_FAILURE, PROMPT_INJECTION_RISK, QUALITY_REVISION_FAILED, FORCED_OVERRIDE.
- Wired every error path in the pipeline to set the appropriate reason using the enum.
- Built a human-readable explanation builder that maps each reason to a descriptive string.

### Phase 7: Encrypted API Key Management
- Implemented per-user Fernet-encrypted API key storage with PostgreSQL persistence.
- Built key CRUD endpoints (save, list, delete, validate) with automatic key hint generation.
- Added provider auto-detection that checks for configured API keys when no provider is specified.

### Phase 8: Frontend Dashboard
- Built a Next.js 16 single-page app with three tabs: Playground (chat interface), Analytics (ROI KPIs), Audit Ledger (full history).
- Created animated cascade pipeline visualization showing Tier 1 → confidence gate → escalation → Tier 2 flow.
- Added cost audit card with per-tier spend breakdown, savings percentage, and spend justification text.
- Built API key management modal with per-provider save/test/delete and free-tier setup guide.

---

## Testing

```bash
# Backend tests
cd backend
python -m pytest tests -v

# Frontend build verification
cd frontend
npm run build
```

---

## Deep-Dive Technical Documentation

For in-depth specifications, architectural diagrams, and flowcharts, explore the dedicated documentation guides:

| Document | Description |
|---|---|
| **[Architecture](docs/architecture.md)** | System topology, LangGraph pipeline, database schema, Pareto selection, quality evaluation, cost calculation, and cross-module dependency map |
| **[Workflow](docs/workflow.md)** | End-to-end request flow with sequence diagrams, 10-phase execution breakdown, example scenarios, and state persistence |

---

## License

This project is licensed under the **MIT License**.
