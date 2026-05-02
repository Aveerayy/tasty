# tasty

`tasty` is the runnable product implementation for the caeesar platform vision:
a lineage-first AI governance control plane that sits between AI agents and enterprise systems.

It is designed for low-friction adoption: install fast, run locally, and demo immediately with realistic scenarios.

## Vision and narrative

- Product vision and final landing-copy structure: [`VISION.md`](VISION.md)

## What the product is about

Most AI agent stacks are one-way:

`user prompt -> LLM/agent -> data/tool access -> output/action`

This product supports that model, but it also adds the core differentiator:

`data/lineage/policy change -> trigger -> policy/approval loop -> outbound action`

That reverse-trigger model turns governance signals into safe, auditable automation.

## What is included

- FastAPI control plane service
- Event ingestion endpoint
- Read-only intelligence layer endpoints
- Policy evaluation engine
- Reverse-trigger evaluation engine
- Approval issuance endpoint for governed live execution
- Action execution endpoint (dry-run + simulated live mode)
- In-memory audit/action store
- Starter data contracts for security, finance, healthcare
- API tests for end-to-end trigger flow
- Interactive playground with fake data and side-by-side demo modes
- Out-of-box Docker run for one-command startup

## How the product works

Core flow:

1. **Ingest signal** (`/v1/events/ingest`) from data/lineage/quality events.
2. **Evaluate trigger** (`/v1/triggers/evaluate`) to decide if automation should fire.
3. **Evaluate policy** (`/v1/policy/evaluate`) for allow/deny + approval requirements.
4. **Execute action** (`/v1/actions/execute`) in dry-run or live mode.
5. **Track status** (`/v1/actions/{id}`) with audit references.

Intelligence + governance extensions:

- **List systems** (`/v1/intelligence/systems`) for centralized read-only business context.
- **Query intelligence layer** (`/v1/intelligence/query`) with quality/lineage summary.
- **Issue approval token** (`/v1/approvals/issue`) for high-risk live actions.
- **Register ETL source** (`/v1/etl/sources`) for business-system onboarding.
- **Record ETL run** (`/v1/etl/runs`) to update freshness/quality/lineage signals.

Playground adds orchestration endpoints:

- `GET /v1/playground/scenarios`
- `POST /v1/playground/run`
- `POST /v1/playground/reset`

Quality/trust now influence runtime decisions:

- Trigger thresholds require minimum quality score.
- Policy risk tier (`low|medium|high|critical`) is derived from quality.
- High/critical live actions require valid approval tokens.

## Playground (live product demo)

The playground shows two models side-by-side using fake data:

1. **Today model**: prompt -> agent -> data/tools -> action
2. **Reverse model**: data change -> trigger -> policy/approval -> action

Use it at:

- `http://127.0.0.1:8000/playground`

Playground features:

- Domain examples: security, finance, healthcare
- Fake data scenario presets
- One-click run for both models
- Resettable in-memory state for repeated demos
- Dry-run mode for safe demonstrations

Included scenarios:

- **Security**
  - Critical vulnerability detection
  - Reverse-trigger recommended action: `create_patch_pr`
- **Finance**
  - Payment risk spike
  - Reverse-trigger recommended action: `hold_payment`
- **Healthcare**
  - Clinical data quality alert
  - Reverse-trigger recommended action: `open_data_stewardship_task`

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open docs at `http://127.0.0.1:8000/docs`.
Open playground at `http://127.0.0.1:8000/playground`.

## Out-of-box Docker run

```bash
docker compose up --build
```

Then open:

- API docs: `http://127.0.0.1:8000/docs`
- Playground: `http://127.0.0.1:8000/playground`

## Demo environment setup (for product testing)

### Option A: Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ".[dev]"
uvicorn app.main:app --reload
```

### Option B: Docker

```bash
docker compose up --build
```

### Validate environment

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/v1/playground/scenarios
curl -s "http://127.0.0.1:8000/v1/intelligence/systems?domain=finance"
```

### Register ETL source and ingestion run (example)

```bash
curl -s -X POST http://127.0.0.1:8000/v1/etl/sources \
  -H "Content-Type: application/json" \
  -d '{"sourceId":"src_salesforce_crm","name":"Salesforce CRM","systemType":"salesforce","domain":"finance","connectionMode":"api","owner":"data-platform","metadata":{"region":"us"}}'

curl -s -X POST http://127.0.0.1:8000/v1/etl/runs \
  -H "Content-Type: application/json" \
  -d '{"sourceId":"src_salesforce_crm","recordsExtracted":1000,"recordsLoaded":995,"status":"partial","qualityScore":0.8,"lineageCoverage":0.85,"notes":"minor schema drift handled"}'
```

## Run tests

```bash
pytest -q
```

## Run scenarios from API (today vs reverse)

### Security

```bash
curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"today","domain":"security","scenarioId":"sec-vuln-critical","actor":"demo-user","dryRun":true}'

curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"reverse","domain":"security","scenarioId":"sec-vuln-critical","actor":"demo-user","dryRun":true}'
```

### Finance

```bash
curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"today","domain":"finance","scenarioId":"fin-payment-risk","actor":"demo-user","dryRun":true}'

curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"reverse","domain":"finance","scenarioId":"fin-payment-risk","actor":"demo-user","dryRun":true}'
```

### Healthcare

```bash
curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"today","domain":"healthcare","scenarioId":"hc-data-quality","actor":"demo-user","dryRun":true}'

curl -s -X POST http://127.0.0.1:8000/v1/playground/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"reverse","domain":"healthcare","scenarioId":"hc-data-quality","actor":"demo-user","dryRun":true}'
```

This is the low-friction MVP path: one service, one API contract, one immediate demo surface.

## Why playground design looks like this

This playground follows common API/demo best practices:

- guided scenario flow with executable steps
- isolated fake/sandbox data
- side-by-side comparison mode for product differentiation
- reset/replay support for demos

References:

- [Interactive Playground setup patterns](https://documentation.ai/docs/api-documentation-and-playground/interactive-playground-setup)
- [API sandbox best practices](https://www.digitalapi.ai/blogs/simple-api-sandbox-architecture-how-it-works-best-practices)
- [Live fake-data playground concepts](https://fakeapifordevs.vercel.app/)
- [Webhook simulation ideas for trigger demos](https://webhooksimulator.com/features/simulated-data-generation)
