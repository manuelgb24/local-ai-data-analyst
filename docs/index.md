# 🚀 Local AI Data Analyst
### Can a free local AI replace part of a junior data analyst workflow?

---

## 🎬 Live Demo

[▶ Click here to watch the demo](Demo.mp4)

---

## 🧠 What This Project Does

Local AI Data Analyst is a **local-first AI data analysis product** and a portfolio experiment built around one practical question:

> How much of the early junior data analyst workflow can a free local AI actually take over?

The answer is intentionally not “all of it”. The interesting part is the boundary.

This project tests how far a local stack can go with a spreadsheet or tabular file: load the dataset, profile it, answer a natural-language question, produce a structured explanation, and keep the evidence behind the result.

It can help with repeatable first-pass analysis work:

- load local `csv`, `xlsx`, and `parquet` files;
- profile tabular data through DuckDB;
- answer focused analytical questions;
- generate narrative summaries with a local Ollama model;
- expose tables, chart-ready outputs, SQL traces, and findings;
- persist traceable artifacts per run;
- work through a web UI, local API, or CLI.

The goal is not to pretend that AI replaces accountability. The goal is to show what a free, local, reproducible system can already automate — and where a human analyst is still essential.

---

## ⚙️ How It Works

Local dataset (`csv`, `xlsx`, `parquet`)  
↓  
DuckDB local profiling and analytical queries  
↓  
`data_analyst` agent  
↓  
Local LLM through Ollama (`deepseek-r1:8b`)  
↓  
Narrative answer + findings + tables/charts  
↓  
Traceable local artifacts per run

The web interface is the main product surface, while the local API and CLI keep the project operable, testable, and reproducible.

---

## 🏗 Architecture Overview

The system is intentionally layered:

- 🌐 `interfaces/web` → main local web experience;
- 🔌 `interfaces/api` → local FastAPI surface for health, chats, runs, and artifacts;
- 🧭 `application` → use-case layer shared by UI/API/CLI;
- ⚙️ `runtime` → run coordination and tracking;
- 🤖 `agents/data_analyst` → analytical intelligence;
- 🦆 `data` + DuckDB adapter → local dataset preparation and querying;
- 🧾 `artifacts` → persisted outputs and run traceability;
- 🧰 `interfaces/cli` → technical and operational workflow;
- 🦙 Ollama adapter → local model integration.

This keeps the product surfaces separate from the analytical core, so the repo feels like a real local product rather than a one-off notebook demo.

---

## 🎯 Engineering Highlights

- **Local-first by default**: datasets are referenced by local path and processed on the user's machine.
- **Free local AI workflow**: Ollama + `deepseek-r1:8b` are used by default for the real model path.
- **DuckDB analytics layer**: deterministic profiling and analytical queries are separated from model narration.
- **Single real agent**: `data_analyst` is explicit and focused; there is no fake multi-agent orchestration.
- **Traceable artifacts**: runs produce local evidence such as findings, tables, chart-ready outputs, and metadata.
- **Multiple interfaces**: web UI for users, local API for product integration, CLI for operation and validation.
- **Synthetic demo dataset**: the public repo is designed to be reproducible without private data.

---

## 🧑‍💼 Where The Human Still Matters

This project is deliberately framed as **intrigue, not hype**.

The AI can cover parts of the mechanical junior analyst loop: initial exploration, simple questions, summaries, and traceable reporting. But a human is still needed to:

- choose the right business question;
- detect misleading or incomplete data;
- clean messy real-world datasets;
- judge whether a result is useful, not just plausible;
- add domain context;
- validate the final answer;
- take responsibility for the conclusion.

The strongest version of this product is not “AI replaces the analyst”. It is: **AI handles the repetitive analytical loop while the human keeps the judgment loop**.

---

## 🔒 Why Local-First Matters

Many AI data demos upload files to hosted tools or rely on uncontrolled prompt sessions. This repo demonstrates a different approach:

- data stays local;
- the model workflow is free and local by default;
- there is no hosted backend, auth layer, or multi-user service;
- deterministic DuckDB work is separated from AI narration;
- artifacts make the answer auditable instead of ephemeral;
- the project can be replicated from the public repository.

That makes the project safer to inspect, easier to reproduce, and more honest about what the AI actually did.

---

## 📂 Repository

Explore the full implementation, README, setup instructions, reproducibility notes, and source code here:

[github.com/manuelgb24/local-ai-data-analyst](https://github.com/manuelgb24/local-ai-data-analyst)
