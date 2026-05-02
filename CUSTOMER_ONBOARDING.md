# Customer Onboarding Guide

This guide is the fastest path to onboard a new customer to the caeesar `tasty` platform.

## 1) Onboarding outcome

At the end of onboarding, the customer can:
- Run a persistent Postgres-backed control plane.
- Configure who provides the central data pool.
- Register ETL sources and ingestion telemetry.
- Query unified read-only intelligence.
- Execute governed action flows (today + reverse models).

## 2) Deployment model decision (central pool provider)

Use the platform endpoint to declare the pool ownership model:

- `customer_managed`: customer owns Snowflake/BigQuery/Databricks, caeesar connects to it.
- `platform_managed`: caeesar hosts and operates the data pool for the customer.

API:

```bash
curl -s -X PUT http://127.0.0.1:8000/v1/platform/pool-config \
  -H "Content-Type: application/json" \
  -d '{"provider":"customer_managed","poolType":"warehouse","platform":"snowflake","region":"us","owner":"data-platform","notes":"initial rollout"}'
```

## 3) Day-0 setup checklist

- Provision runtime:
  - Docker + Docker Compose
  - Ports `8000` (API) and `5432` (Postgres)
- Start stack:
  - `docker compose up --build -d`
- Validate:
  - `GET /health`
  - `GET /v1/platform/pool-config`
- Open docs:
  - `http://127.0.0.1:8000/docs`

## 4) Source onboarding checklist

For each source system:
- Define source identity (`sourceId`, `name`, `owner`, `domain`).
- Select connection mode (`api|db|stream|file`).
- Register metadata (region, environment, pii hints, lineage tags).
- Start ETL run telemetry into `/v1/etl/runs`.

Example:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/etl/sources \
  -H "Content-Type: application/json" \
  -d '{"sourceId":"src_salesforce_crm","name":"Salesforce CRM","systemType":"salesforce","domain":"finance","connectionMode":"api","owner":"data-platform","metadata":{"region":"us"}}'
```

## 5) Governance rollout checklist

- Policy:
  - Validate risk-tier behavior (`low|medium|high|critical`).
  - Confirm high/critical live actions require approvals.
- Access:
  - Enable API-key auth in production-like environments.
  - Validate RBAC mappings (`admin`, `operator`, `approver`, `steward`).
- Trigger:
  - Validate quality thresholding for reverse-trigger actions.
- Execution:
  - Test dry-run first, then controlled live actions.
  - Configure webhook connector and retry limits for live actions.
- Audit:
  - Confirm action IDs and approval IDs are traceable.

## 6) Demo to production path

- Week 1: one domain in demo mode (security or finance).
- Week 2: wire one real ETL source and production-like telemetry.
- Week 3: enforce approvals for high-risk actions.
- Week 4: activate reverse workflows in controlled scope.

## 7) Operations runbook (minimum)

- Backup Postgres volume.
- Monitor API health + ETL run freshness.
- Rotate approver identities and access.
- Review policy overrides and high-risk action history weekly.
