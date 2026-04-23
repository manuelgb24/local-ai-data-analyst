# Local AI Data Analyst

How much of a junior data analyst workflow can a free local AI actually cover?

This repository is my attempt to test that question with a real, reproducible local product. It does not claim that AI fully replaces analysts. It asks a narrower and more useful question: how far can a local model, DuckDB and a disciplined product workflow go before human judgment becomes essential again?

The answer this project explores is intentionally practical. A free local AI can help with initial dataset exploration, profiling, simple analytical questions, SQL-backed summaries and traceable reports. It still needs a human for business context, ambiguous decisions, data quality judgment and final responsibility.

That tension is the point of the project.

---

## The question behind this project

Junior data analysis work often starts with repeatable tasks: load a spreadsheet, understand the columns, ask basic questions, calculate grouped metrics, summarize patterns and package the result in a form someone else can inspect.

Those tasks are exactly where local AI is becoming interesting.

I built Local AI Data Analyst to turn that question into something measurable instead of theoretical. The system keeps the dataset on your machine, loads it into DuckDB, runs a focused analytical agent, asks a local Ollama model to explain the results, and stores every output behind the answer as traceable artifacts.

The goal is not to make another notebook demo. The goal is to show how a free local AI stack can cover part of the junior analyst loop while keeping the engineering boundaries clear.

---

## What the AI can handle

In its current form, the product can cover a useful slice of early analytical work:

- load local `csv`, `xlsx` and `parquet` files;
- profile the dataset through DuckDB;
- answer natural-language questions against one selected dataset;
- produce narrative explanations from structured results;
- return findings, SQL traces, tables, chart-ready data and artifact references;
- keep runs and chats persistent enough to inspect later;
- expose the same analytical core through a web UI, local API and CLI.

This makes it useful for first-pass exploration and repeatable local analysis, especially when the dataset should not be uploaded to a hosted service.

---

## What still needs a human

The project is deliberately honest about the boundary.

A local AI analyst can accelerate the mechanical parts of analysis, but it does not own the conclusion. A human still matters for:

- deciding which business question is worth asking;
- spotting misleading data or missing context;
- cleaning ambiguous or messy source files;
- validating whether an answer is useful, not just plausible;
- making decisions that require domain knowledge;
- taking responsibility for the final recommendation.

So the project is not framed as “AI replaces analysts”. It is framed as: **which parts of junior analyst work can be automated locally, for free, and with evidence behind every answer?**

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

## Replicate locally in 5 minutes

Clone the repository:

```bash
git clone https://github.com/manuelgb24/local-ai-data-analyst.git
cd local-ai-data-analyst
```

Install Python and web dependencies:

```bash
python -m pip install -r requirements-dev.txt
npm ci --prefix interfaces/web
```

Install the local model required for real AI analysis:

```bash
ollama pull deepseek-r1:8b
```

Build and start the local product:

```bash
npm --prefix interfaces/web run build
python -m interfaces.api --serve-web
```

Open:

```text
http://127.0.0.1:8000
```

You can validate most of the project without Ollama running:

```bash
python scripts/ci_checks.py python
python scripts/ci_checks.py web
```

For real AI analysis and smoke checks, Ollama must be running locally and `deepseek-r1:8b` must be available.

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
docs/              Portfolio page and GitHub Pages entrypoint
runtime/           Run coordination and tracking
tests/             Unit, integration, E2E and smoke tests
```

---

## Security and privacy notes

This repository is designed to be reproducible without publishing private data.

- The committed demo dataset is synthetic: `DatasetV1/demo_business_metrics.csv`.
- Real user datasets are loaded from local filesystem paths at runtime.
- Generated chats, runs and artifacts stay in the local artifact store.
- Generated outputs are ignored by git through `.gitignore`.
- The default model workflow uses local Ollama, not an external AI API.
- The project does not require a hosted backend, authentication system or multi-user service.
- Do not commit private datasets, `.env` files, credentials, API keys or generated artifacts.

Before publishing changes, check:

```bash
git status --short
git ls-files | grep -E '(^|/)(\.env|.*\.pem|.*\.key|.*secret.*|.*token.*|.*credential.*|.*password.*)$'
```

The second command should return no tracked sensitive files.

---

## If this were production

The next hardening layer would focus on:

- packaged installers or a one-command local launcher;
- stricter artifact retention controls;
- richer local observability;
- clearer model readiness diagnostics;
- additional specialist analysis workflows once the product surface needs them.

The foundation is already there: local data, explicit execution, traceable artifacts and a product surface that is useful before it becomes complex.

---

## License

MIT.
