# Product Report: tasty (Core Product + Playground)

## Objective

Deliver a usable, installable, low-friction product that demonstrates:

- Today model: prompt-driven agent workflow
- Reverse model: data-change-driven triggered workflow

Both are available in the same playground for direct comparison, which is essential for product demos, onboarding, and technical evaluations.

## Product definition

`tasty` is the product implementation of the caeesar platform concept:

- A governance control plane for agentic systems
- A lineage- and policy-aware trigger engine
- A playground that proves value without production dependencies

Primary value:

1. Centralized control for AI agent actions
2. Traceable execution with policy loops
3. Reverse-trigger automation from data changes
4. Fast adoption via fake-data demo environment

## What was added

### Product capabilities

- Event ingestion, trigger evaluation, policy evaluation, action execution, action status.
- ETL source registration and ETL run telemetry for data-pool onboarding.
- Reverse-trigger orchestration for security, finance, and healthcare.
- Scenario-based fake data demos.
- Side-by-side model comparison for current vs proposed architecture.
- Centralized read-only intelligence layer over business systems.
- Quality-aware trigger decisions and risk-tier policy decisions.
- Explicit approval token flow for high-risk live execution.

### Playground capabilities

- `/playground` interactive UI.
- Side-by-side execution for:
  - Today model
  - Reverse model
- Scenario presets and domain selector.
- Resettable state for repeated product demos.
- API-backed execution with auditable step-by-step responses.

### Installability and adoption

- Local Python quickstart.
- Docker out-of-box startup with `docker compose up --build`.
- No external infra required for first demo.
- One URL demo surface: `/playground`.

## Why this implementation is low friction

- Single service, no mandatory external dependencies.
- Works with fake data out of the box.
- Demo value visible in minutes.
- Safe by default via dry-run execution.
- API and playground both available immediately.
- Supports both UI demo and API-only testing styles.

## Product architecture (current)

Components:

- **API layer** (`app/main.py`)
- **Intelligence layer** (`app/intelligence.py`)
- **Policy engine** (`app/policy.py`)
- **Trigger engine** (`app/triggers.py`)
- **Execution service** (`app/executor.py`)
- **Store + audit** (`app/store.py`)
- **Playground orchestrator** (`app/playground_service.py`)
- **Playground UI** (`app/static/playground.html`)

This allows a complete end-to-end run path with no external broker or database for first deployment.

## New API endpoints (this iteration)

- `GET /v1/intelligence/systems`
- `POST /v1/intelligence/query`
- `POST /v1/approvals/issue`
- `POST /v1/etl/sources`
- `GET /v1/etl/sources`
- `POST /v1/etl/runs`
- `GET /v1/etl/runs`

These complement existing ingestion/trigger/policy/action endpoints.

## Demo environment setup

### Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ".[dev]"
uvicorn app.main:app --reload
```

### Docker setup

```bash
docker compose up --build
```

### Access points

- API docs: `http://127.0.0.1:8000/docs`
- Playground: `http://127.0.0.1:8000/playground`
- Health: `http://127.0.0.1:8000/health`

## Demo scripts

### Security

1. Run today model: operator asks agent to check vulnerabilities.
2. Run reverse model: vulnerability event triggers fix workflow.
3. Compare steps and governance loops.

### Finance

1. Simulate payment risk spike via scenario `fin-payment-risk`.
2. Run today model to show prompt-driven action path.
3. Run reverse model to trigger `hold_payment`.
4. Compare trigger confidence and governance step differences.

### Healthcare

1. Simulate clinical data quality alert via scenario `hc-data-quality`.
2. Run today model to show prompt-driven stewardship flow.
3. Run reverse model to trigger `open_data_stewardship_task`.
4. Compare approval requirement and execution behavior.

## API examples for scenario testing

### Scenario catalog

```bash
curl -s http://127.0.0.1:8000/v1/playground/scenarios
```

### Run today model

```bash
curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"today","domain":"security","scenarioId":"sec-vuln-critical","actor":"demo-user","dryRun":true}'
```

### Run reverse model

```bash
curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"reverse","domain":"security","scenarioId":"sec-vuln-critical","actor":"demo-user","dryRun":true}'
```

### Reset demo state

```bash
curl -s -X POST http://127.0.0.1:8000/v1/playground/reset
```

## Next implementation steps

1. Persist store to Postgres.
2. Add explicit approval endpoints and state transitions.
3. Add webhook/adapter execution connectors.
4. Add request history and shareable playground run links.
5. Add OpenAPI-generated request forms in the playground.
