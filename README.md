
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

# AI Analysis Architecture


## 🎯 Intake Agent
Processes the initial query (e.g., `"analyze amzn"`) by utilizing the `ticker_validator.py` tool to perform fuzzy-matching and ticker validation. It uses an LLM to classify user intent into required analysis types like fundamental, sentiment, or quant, producing a structured `AnalysisRequest` that initializes the graph state.

## 🧠 Supervisor
Acts as the orchestrator of the LangGraph workflow defined in `graph_builder.py`. It reads the `AnalysisRequest` to generate a specific `ExecutionPlan` for worker agents. It manages parallel dispatching and handles re-research loops if the Synthesis Agent provides a critique requiring more data.

## 📊 Fundamental Analyst
Conducts deep-dive financial research. It uses the `financial_data_tool.py` (via `yFinance`) to fetch live ratios such as P/E and Debt-to-Equity. It also employs the `sec_edgar_tool.py`, which uses `BeautifulSoup` to surgically scrape the SEC EDGAR database for MD&A and Risk Factors from the latest 10-K/10-Q filings.

## 💬 Sentiment Analyst
Evaluates market narrative and catalysts. It utilizes the `enhanced_news_fetcher.py` tool to extract news from Finnhub and Tavily. Crucially, it also calls the `macro_context_tool.py` to pull real-time economic indicators (CPI, GDP, Interest Rates) from the Federal Reserve FRED API to provide the `"big picture"` context for the sentiment report.

## 📈 Quant Coder
An agentic coder that dynamically generates Python scripts for technical analysis. The generated code is first inspected by the `ast_analyzer.py` for security vulnerabilities and is then executed in a Secure Docker Sandbox via the `sandbox_executor.py`. It produces professional technical dashboards and charts (saved to the `charts/` directory) using `pandas` and `matplotlib`.

## ⚠️ Risk Validator
Performs a final audit on all analyst findings. It computes a `Contradiction Score` to identify conflicting conclusions between fundamental and sentiment data. It also runs a `Data Freshness Audit` to ensure all source data is current before the synthesis step.

## 🔮 Synthesis Agent
The intellectual core of the system. It generates an initial investment thesis, critiques it from the perspective of a skeptical Portfolio Manager, and produces a final `confidence_score`. If the score is below the required threshold, it issues a `re_research_request` to the Supervisor to restart the cycle.

## 👤 Human-in-the-Loop Checkpoint
A safety gate that utilizes LangGraph's `interrupt_before` functionality. The graph execution halts, allowing you to review the synthesis, confidence score, and contradiction flags in the Streamlit UI before the final report is compiled.

## 📝 Report Compiler
Finalizes the process by formatting all approved data into a structured Markdown report. It uses Llama 3 (via the `nvidia_nim_client.py`) to ensure an institutional-grade tone and intelligently omits sections if specific source data was missing or unavailable.

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


