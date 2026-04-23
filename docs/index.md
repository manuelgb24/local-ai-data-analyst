# 🚀 Can a free local AI replace part of a junior data analyst workflow?

### Local AI Data Analyst is my attempt to test that question with a real, reproducible product.

---

## 🔎 The Experiment

This project asks a practical question instead of making a vague AI claim:

> How much of the early junior data analyst workflow can a free local AI actually take over?

The answer is not “all of it”. The interesting part is the boundary.

Local AI Data Analyst tests how far a local stack can go with a spreadsheet or tabular file: load the dataset, profile it, answer a natural-language question, produce a structured explanation, and keep the evidence behind the result.

Everything is designed to run locally:

- no hosted backend;
- no external AI API by default;
- no multi-user system;
- no data leaving the machine;
- no hidden claim that the model owns the final decision.

---

## 🧠 What It Can Do

The shipped specialist is `data_analyst`.

It can help with the repeatable parts of early analytical work:

- load local `csv`, `xlsx`, and `parquet` files;
- profile tabular data through DuckDB;
- answer focused analytical questions;
- generate narrative summaries with a local Ollama model;
- expose tables, chart-ready outputs, SQL traces, and findings;
- persist traceable artifacts per run;
- work through a web UI, local API, or CLI.

That makes it useful for first-pass exploration, reproducible local analysis, and portfolio-grade experimentation with AI-assisted analytics.

---

## 🧑‍💼 Where The Human Still Matters

This project is intentionally not framed as “AI fully replaces analysts”.

A human is still needed to:

- choose the right business question;
- detect misleading or incomplete data;
- clean messy real-world datasets;
- judge whether a result is useful, not just plausible;
- add domain context;
- take responsibility for the conclusion.

The product is strongest when the AI handles the mechanical loop and the human keeps the judgment loop.

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

---

## 🏗 Architecture Overview

The system is intentionally layered:

- 🌐 `interfaces/web` → main local web experience
- 🔌 `interfaces/api` → local FastAPI surface for health, chats, runs, and artifacts
- 🧭 `application` → use-case layer shared by UI/API/CLI
- ⚙️ `runtime` → run coordination and tracking
- 🤖 `agents/data_analyst` → analytical intelligence
- 🦆 `data` + DuckDB adapter → local dataset preparation and querying
- 🧾 `artifacts` → persisted outputs and run traceability
- 🧰 `interfaces/cli` → technical and operational workflow
- 🦙 Ollama adapter → local model integration

The architecture keeps product surfaces separate from the analytical core, so the current system is simple without being a throwaway prototype.

---

## 🔒 Why Local-First Matters

Many AI data demos upload files to hosted services or rely on uncontrolled prompt sessions.

This project demonstrates a different approach:

- keep data local;
- use a free local model workflow by default;
- separate deterministic data work from model narration;
- make execution reproducible;
- persist the evidence behind each answer;
- expose the system as a usable local product.

---

## ▶️ View The Source And Run It Locally

Explore the full implementation and reproduction steps in the main repository:

[github.com/manuelgb24/local-ai-data-analyst](https://github.com/manuelgb24/local-ai-data-analyst)
