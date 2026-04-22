# 🚀 Local AI Data Analyst  
### Local-First AI Data Analysis Agent

---

## 🎬 Live Demo

[▶ Aquí se pega el vídeo](Demo.mp4)

---

## 🧠 What This Project Does

This project implements a **local-first AI data analyst** for exploring spreadsheet and tabular files directly from your own machine.

A user can select a local dataset, ask an analytical question, and get a structured response backed by DuckDB queries, a local LLM, persisted artifacts, and a web interface designed for real usage instead of one-off prompts.

The shipped specialist is `data_analyst`.

Everything is designed to run locally:

- no hosted backend;
- no external AI API by default;
- no multi-user system;
- no data leaving the machine.

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
Narrative answer + tables/charts  
↓  
Traceable local artifacts per run

The user can interact with the system through the web UI, the local API, or the CLI.

---

## 🏗 Architecture Overview

The system is intentionally layered:

- 🌐 `interfaces/web` → main local web experience
- 🔌 `interfaces/api` → local FastAPI surface for health, chats, runs and artifacts
- 🧭 `application` → use-case layer shared by UI/API/CLI
- ⚙️ `runtime` → run coordination and tracking
- 🤖 `agents/data_analyst` → analytical intelligence
- 🦆 `data` + DuckDB adapter → local dataset preparation and querying
- 🧾 `artifacts` → persisted outputs and run traceability
- 🧰 `interfaces/cli` → technical and operational workflow
- 🦙 Ollama adapter → local model integration

The architecture keeps product surfaces separate from the analytical core, so the current system is simple without being a throwaway prototype.

---

## 🎯 Engineering Highlights

- Local-first data analysis product
- Web UI + local API + CLI over the same core
- DuckDB-backed tabular analysis
- Local Ollama model integration
- Synthetic reproducible demo dataset
- Persistent runs, chats and artifacts
- Structured responses with narrative, findings, SQL traces, tables and charts
- Unit, integration, E2E and smoke validation lanes
- Clear architectural boundaries between interface, application, runtime, agent, data, artifacts and adapters

---

## 🤝 AI-Assisted Engineering

This repository includes `AGENTS.md` because the project was developed with AI assistance under explicit engineering rules.

That file documents the collaboration constraints used to keep the work disciplined: local-first scope, one real agent, no hidden planner, no automatic routing, no hosted backend, and no accidental multi-agent expansion.

The point is not only that AI helped write code. The point is that AI was used inside a controlled engineering process.

---

## 🔒 Why This Matters

Many AI data demos send files to hosted services or rely on uncontrolled prompt sessions.

This project demonstrates a different approach:

- keep data local;
- make execution reproducible;
- separate deterministic data work from model narration;
- persist the evidence behind each answer;
- expose the system as a usable local product.

It is a small product surface built on engineering discipline, not just a prompt demo.

---

## 📂 Repository

Explore the full implementation in the main repository:

[github.com/manuelgb24/local-ai-data-analyst](https://github.com/manuelgb24/local-ai-data-analyst)
