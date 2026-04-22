# Local AI Data Analyst

A local-first AI data analyst for exploring spreadsheet and tabular files from your own machine.

This project turns a local dataset into an interactive analytical workspace: point the system to a file, ask a question in natural language, let DuckDB handle the data work, let a local Ollama model explain the results, and keep every output traceable through persisted artifacts.

The goal is not to make another notebook demo. The goal is to show how an AI data product can be built with clear boundaries, reproducible execution and local infrastructure discipline from the start.

---

## Why this exists

Analyzing a dataset is often more scattered than it should be.

You inspect the file in a spreadsheet, move to SQL for aggregation, open a notebook for charts, copy context into a model, then manually track which result came from which data slice. That works for exploration, but it is hard to reproduce and easy to lose.

I built this project to turn that workflow into a small local product.

The system keeps the dataset on your machine, loads it into DuckDB, runs a focused analytical agent, generates a human-readable answer, and stores the technical outputs behind the response. The web UI makes the experience usable; the local API makes it operable; the CLI keeps the technical workflow accessible.

---

## What this repository implements

- A shipped analytical agent: `data_analyst`
- A local web interface for analytical chats
- A local FastAPI API for health, chats, runs and artifacts
- A CLI for operational and technical workflows
- Local dataset loading for `csv`, `xlsx` and `parquet`
- DuckDB-backed profiling and analytical queries
- Ollama integration with `deepseek-r1:8b`
- Persistent local run metadata and artifacts
- A small synthetic demo dataset in `DatasetV1/demo_business_metrics.csv`
- Automated Python and web validation lanes

The current product surface is:

```text
interfaces/web -> interfaces/api -> application -> runtime -> agents/data_analyst -> data / artifacts / adapters
interfaces/cli -> application -> runtime -> agents/data_analyst -> data / artifacts / adapters
```

---

## Design philosophy

This project is built around controlled analysis rather than uncontrolled generation.

The model is not responsible for magically reading files by itself. The system first prepares the dataset locally, profiles it, executes deterministic DuckDB operations where possible, and then asks the model to explain the result in a useful way. That separation keeps the product easier to inspect, test and extend.

Every run leaves a trail: the user prompt, the dataset path, generated findings, SQL traces, tables, charts and artifact references. The goal is to make AI-assisted data analysis feel like a product workflow instead of a disposable prompt session.

---

## Built to grow

The first shipped specialist is `data_analyst`, focused on local tabular analysis. The repository structure is intentionally layered so future analytical specialists can be added without rewriting the web interface, API, runtime, data preparation or artifact system.

That is the main architectural point of the project: the current experience is simple, but the boundaries are strong enough for the system to evolve.

---

## How the system works

1. The user selects a local demo dataset or enters a local file path.
2. The API creates a run or continues an analytical chat.
3. The runtime prepares the dataset and coordinates execution.
4. DuckDB handles local profiling, previews and analytical queries.
5. `data_analyst` combines structured results with the user question.
6. Ollama runs `deepseek-r1:8b` locally to synthesize the response.
7. The system persists the answer, metadata, tables, charts and traceable artifacts.

---

## Local-first architecture

### Web UI

`interfaces/web` is the main user-facing surface. It lets you create and revisit local analytical chats, select a demo dataset or enter a manual local path, inspect readiness and review embedded chart/table outputs.

### Local API

`interfaces/api` exposes local HTTP contracts for:

- application health;
- provider readiness;
- local dataset listing;
- chat creation and continuation;
- run history;
- artifact inspection.

### Core runtime

The `application` and `runtime` layers coordinate a run without coupling the UI/API to the agent internals.

### Data analyst agent

`agents/data_analyst` contains the analytical behavior. It profiles the dataset, builds deterministic DuckDB queries where possible, calls the local model for narrative synthesis and returns structured findings, SQL traces, tables, charts and artifact references.

### Adapters

`adapters` isolates external dependencies such as DuckDB and Ollama.

---

## Requirements

- Python 3.13 recommended
- Node.js 22 recommended for the web UI
- npm
- Ollama running locally
- Ollama model: `deepseek-r1:8b`

Install or pull the model with Ollama before running real AI analysis:

```bash
ollama pull deepseek-r1:8b
ollama list
```

---

## Setup

### 1. Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

For tests and validation:

```bash
python -m pip install -r requirements-dev.txt
```

### 2. Install web dependencies

```bash
npm --prefix interfaces/web install
```

### 3. Build the web UI

```bash
npm --prefix interfaces/web run build
```

### 4. Start the packaged local product

```bash
python -m interfaces.api --serve-web
```

Open:

```text
http://127.0.0.1:8000
```

The API is served from the same local process.

---

## Quick start

### Run through the CLI

```bash
python -m interfaces.cli --agent data_analyst --dataset DatasetV1/demo_business_metrics.csv --prompt "Which region generated the highest revenue?"
```

### Check operational readiness

```bash
python -m interfaces.cli status
python -m interfaces.cli config
```

### Start only the API

```bash
python -m interfaces.api
```

Useful endpoints:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/proveedor
curl http://127.0.0.1:8000/datasets/local
curl http://127.0.0.1:8000/chats
curl http://127.0.0.1:8000/runs
```

### Run the web UI in development mode

Start the API first:

```bash
python -m interfaces.api
```

Then start Vite:

```bash
npm --prefix interfaces/web run dev
```

Open:

```text
http://127.0.0.1:4173
```

---

## Demo dataset

The repository includes one clean synthetic dataset:

```text
DatasetV1/demo_business_metrics.csv
```

It contains fictional business metrics by date, region, channel and product. It exists only to make the project immediately reproducible.

For your own analysis, use a local path to any supported `csv`, `xlsx` or `parquet` file. Generated chats and runs are intentionally ignored by git.

---

## Validation

Run the Python validation lane:

```bash
python scripts/ci_checks.py python
```

Run the web validation lane:

```bash
python scripts/ci_checks.py web
```

Run real local smoke checks only when Ollama and `deepseek-r1:8b` are available:

```bash
python scripts/ci_checks.py smoke
```

Note for Windows sandboxed environments: `npm --prefix interfaces/web run build` can fail with `spawn EPERM` because of sandbox/tooling restrictions. In that case, validate the web lane from the host environment or with elevated permissions instead of treating it as a product regression.

---

## Repository structure

```text
adapters/          External integrations such as DuckDB and Ollama
agents/            The data_analyst agent
application/       Use-case contracts and application-level models
artifacts/         Persistence code for runs/chats; generated outputs are gitignored
data/              Local dataset loading and preparation
interfaces/api/    Local FastAPI surface
interfaces/cli/    Operational CLI
interfaces/web/    React/Vite web UI
docs/              Portfolio page and demo video placeholder for GitHub Pages
runtime/           Run coordination and tracking
tests/             Unit, integration, E2E and smoke tests
```

---

## Security and privacy notes

- Datasets are loaded from local paths.
- Generated run/chat artifacts stay local and are ignored by git.
- The default workflow runs against local files and a local Ollama model.
- Generated outputs stay in the local artifact store and are ignored by git.
- Do not commit private datasets, `.env` files, credentials or generated artifacts.

---

## If this were production

The next hardening layer would focus on:

- packaged installers or a one-command local launcher;
- stricter artifact retention controls;
- richer local observability;
- clearer model readiness diagnostics;
- additional specialized analytical agents once the product surface needs them.

The foundation is already there: local data, explicit execution, traceable artifacts and a product surface that is useful before it becomes complex.

---

## License

MIT.
