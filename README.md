
---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a1a2e,50:16213e,100:0f3460&height=220&section=header&text=Auto-Quant%20Financial%20Analyst&fontSize=46&fontColor=ffffff&fontAlignY=40&desc=Enterprise-Grade%20Multi-Agent%20Hedge%20Fund%20Intelligence&descAlignY=60&descSize=17&descColor=93c5fd" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent_Graph-FF4B4B?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-Llama_3.1_405B-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live_Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Sandboxed_Execution-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Redis](https://img.shields.io/badge/Redis-68x_Faster_Cache-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)

<br/>

> **Auto-Quant is not a chatbot wrapper around Yahoo Finance.**
>
> It is a team of specialized AI agents that autonomously fetch SEC filings,
> parse Federal Reserve macroeconomic data, read news from multiple angles,
> and then **argue with themselves** until they are confident enough to hand
> you an institutional-grade investment memo.

<br/>

[🎥 Watch the Demo](#-demo) · [⚡ Performance](#-performance) · [🧠 How It Works](#-how-it-works) 

</div>

---

## 🎥 Demo

[➡️ **Watch the Full Demo on YouTube**](https://www.youtube.com/watch?v=g7hQ68o5_7A)

A full end-to-end analysis of NVIDIA—from raw query to a final, downloadable PDF report. Watch the live execution terminal as the self-healing loop triggers when the AI decides its own first-pass analysis isn't good enough.

---

# Architecture

<p align="center">
  <img width="585" height="796" alt="graph_architecture" src="https://github.com/user-attachments/assets/9104741e-9171-4861-a4bf-e3ddbb98e1b1" />
</p>

---

## 📸 Screenshots


| Live Agent Dashboard | Human Review Checkpoint |
|:---:|:---:|
| <img width="400" alt="Live Agent Dashboard" src="https://github.com/user-attachments/assets/6e57e8e2-6990-4a6b-aaf1-cfb0e7264178" /> | <img width="400" alt="Human Review Checkpoint" src="https://github.com/user-attachments/assets/98dbbec2-1f55-41f8-808f-ccaa61ae7561" /> |

| Generated Technical Charts | Final Investment Memo |
|:---:|:---:|
| <img width="400" alt="Generated Technical Charts" src="https://github.com/user-attachments/assets/2899dd15-69ab-475b-8534-42323921d14f" /> | <img width="400" alt="Final Investment Memo" src="https://github.com/user-attachments/assets/15ccd505-a6d9-48bd-b131-fa2841ca5b88" /> |


## 🧠 How It Works

Auto-Quant runs as a **directed state machine** (via LangGraph)—not a chaotic ReAct loop. Every agent has a fixed responsibility, a typed input contract, and a typed output contract. No agent passes raw text to another agent; every handoff is Pydantic-validated.

Here is the exact journey of a query from input to report.

### The Agent Roster

**🎯 Intake Agent** — Receives your raw query (`"analyze amzn"`). Validates and fuzzy-matches the ticker. Uses an LLM to classify intent into a list of required analyses (e.g., `['fundamental', 'sentiment']`). Produces a structured `AnalysisRequest` object that seeds the entire graph.

**🧠 Supervisor** — Reads the `AnalysisRequest` and the user's specific questions. Generates a typed `ExecutionPlan` with specific instructions for each worker. Dispatches research workers **in parallel** using LangGraph's `Send()` API. If a re-research loop is triggered, the Supervisor reads the critique and generates a new, targeted plan.

**📊 Fundamental Analyst** — Fetches live fundamental ratios from yFinance. Surgically scrapes the SEC EDGAR database to extract the **Management's Discussion & Analysis (MD&A)** and **Risk Factors** from the latest 10-K/10-Q. It forces the LLM to cross-examine management's narrative against the raw numbers. Returns a typed `FundamentalReport`.

**💬 Sentiment Analyst** — Uses an LLM to generate 3-4 distinct NewsAPI queries (bull case, bear case, sector trends) to get a 360-degree view. Fetches and deduplicates all articles. Pulls live interest rates and CPI from the Federal Reserve FRED API to add macro context. Returns a `SentimentReport`.

**📈 Quant Coder** — **100% Deterministic & Safe.** This agent does *not* use an LLM to write code. It uses hardcoded Python and `pandas` to calculate all technical indicators (SMA-50, SMA-200, RSI-14). It then uses a robust `matplotlib` function to generate a professional, multi-panel dashboard. The LLM is only used to write the English-language technical summary. This guarantees 100% reliability and zero risk of code-generation failure.

**⚠️ Risk Validator** — Receives all three worker reports. Computes a Contradiction Score (0.0-1.0) across their conclusions. Runs a Data Freshness Audit on all sources. Produces an `overall_risk_level` and a plain-English description of the primary contradiction.

**🔮 Synthesis Agent** — The intellectual core. It runs a 3-step prompt chain:
1.  **Draft:** Generates an initial investment thesis.
2.  **Critique:** Adopts a *Skeptical Senior Portfolio Manager* persona, critiques its own draft, and assigns an initial confidence score.
3.  **Revise & Finalize:** Incorporates the critique and produces the final thesis text and the final, official `confidence_score`. If this score is below 65, the `re_research_request` from the critique step is passed back to the Supervisor.

**👤 Human-in-the-Loop Checkpoint** — Graph execution physically halts here using LangGraph's `interrupt_before`. You see the final confidence score, any contradiction flags, and the thesis draft. The pipeline does not continue without your approval.

**📝 Report Compiler** — Receives the approved synthesis and formats a full structured Markdown report using Llama 3.1 8B. It intelligently omits sections if their source data was unavailable (e.g., no Quant data).

---

## ⚡ Performance

### Redis Caching — 68x Faster Data Retrieval

Financial data does not change every 30 seconds. Every external API response is cached in Redis with a time-to-live (TTL).

```
Data Pipeline Benchmark — All Sources (SEC, yFinance, FRED, NewsAPI) — NVDA

  Run 1  (Cache Miss — live network)   13.53 seconds
  Run 2  (Cache Hit — Redis memory)     0.20 seconds

  Performance Gain:   68x faster
  Latency Reduction:  98.5%
```

This is critical during re-research loops. When the Synthesis Agent requests a second pass, all data is fetched instantly. The expensive Llama 405B model spends its entire inference budget answering the new specific question—not waiting on HTTP.

---

## 🛡️ Security

While the current Quant Coder is 100% deterministic, the architecture retains a full, dormant sandboxing system designed for safely executing LLM-generated code. This demonstrates an enterprise-ready security posture.

The four-layer defense system includes:
1.  **AST Import Allowlist** — Code is parsed to an abstract syntax tree. Any import not on the `matplotlib`-only allowlist causes an immediate rejection.
2.  **Docker Sandbox** — The execution environment is a minimal Python image with `--network none`, strict memory/CPU limits, a read-only filesystem (except `/charts`), and a 30-second hard timeout. The container is destroyed immediately after use.
3.  **Output Validation** — A post-execution check verifies that a valid `.png` file was actually created at the expected path. A "false positive" (code runs but produces no file) triggers a retry.

---

## 🗂️ Project Structure

```
├── app/
│   └── main.py                 # Streamlit UI
├── charts/                     # Generated technical charts (gitignored)
│   └── .gitkeep                # Keeps the folder in the repo
├── sandbox/                    # Isolated environment for code execution
│   ├── Dockerfile              # Container definition
│   └── requirements.txt        # Sandbox-specific dependencies
├── src/                        # Core Application Logic
│   ├── agents/                 # Specialized AI Analysts
│   ├── graph/                  # LangGraph workflow & state
│   ├── llm/                    # NVIDIA NIM client wrappers
│   ├── memory/                 # Redis and Vector store logic
│   ├── security/               # AST analysis for code safety
│   ├── tools/                  # Financial, SEC, and News tools
│   └── utils/                  # Config, Logging, and Plotting
├── .gitignore                  # Cleaned exclusion list
├── docker-compose.yml          # Infrastructure orchestration
├── pyproject.toml              # Project metadata & dependencies
└── graph_architecture.png

```

---


