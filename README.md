# tasty

Implementation-first product foundation for `caeesar` style lineage-first AI governance.

## What is included

- FastAPI control plane service
- Event ingestion endpoint
- Policy evaluation engine
- Reverse-trigger evaluation engine
- Action execution endpoint (dry-run + simulated live mode)
- In-memory audit/action store
- Starter data contracts for security, finance, healthcare
- API tests for end-to-end trigger flow

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open docs at `http://127.0.0.1:8000/docs`.

## Run tests

```bash
pytest -q
```

## First scenario (security)

1. Ingest event `critical_vulnerability_detected`.
2. Evaluate triggers with rule set `security-default`.
3. Evaluate policy for recommended action `create_patch_pr`.
4. Execute action in dry-run mode.
5. Query action status.

This is the low-friction MVP path: one service, one API contract, one vertical domain loop.
