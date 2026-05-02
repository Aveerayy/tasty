# Demo Environment Guide

This environment demonstrates the full platform:
- Foundation ETL + data-pool onboarding
- Unified intelligence queries
- Governed action-taking agents
- Reverse-trigger workflows with approvals
- Persistent Postgres-backed state across restarts

## Start environment

```bash
docker compose up --build -d
```

Optional security/reliability toggles:

```bash
export AUTH_ENABLED=true
export CONTROL_PLANE_API_KEY="replace-with-secure-key"
export ACTION_WEBHOOK_URL="https://your-orchestrator.example.com/actions"
export ACTION_MAX_RETRIES=2
```

## Verify services

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/v1/platform/pool-config
```

## Open interfaces

- API docs: `http://127.0.0.1:8000/docs`
- Playground: `http://127.0.0.1:8000/playground`

## Run one-command smoke demo

```bash
bash scripts/demo_smoke.sh
```

## What persists now

With `DATABASE_URL` set (Docker default), these entities persist:
- Events
- Actions and action status updates
- Approvals
- ETL sources
- ETL runs
- Intelligence-system metrics derived from ETL runs
- Platform pool configuration

## Demonstration sequence for buyers

1. Set central pool provider (`customer_managed` or `platform_managed`).
2. Register ETL source and record run.
3. Show intelligence summary movement from ETL quality updates.
4. Run security reverse scenario in playground.
5. Show approval requirement for high-risk live action.
6. Restart stack and show state still exists.

## Restart persistence validation

```bash
docker compose restart tasty
curl -s "http://127.0.0.1:8000/v1/etl/sources?domain=finance"
curl -s "http://127.0.0.1:8000/v1/etl/runs?sourceId=src_demo_finance"
```

## Shutdown

```bash
docker compose down
```

To fully reset state, remove volume:

```bash
docker compose down -v
```
