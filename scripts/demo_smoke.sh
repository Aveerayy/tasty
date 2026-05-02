#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "Health:"
curl -s "${BASE_URL}/health"
echo

echo "Set pool config:"
curl -s -X PUT "${BASE_URL}/v1/platform/pool-config" \
  -H "Content-Type: application/json" \
  -d '{"provider":"customer_managed","poolType":"warehouse","platform":"snowflake","region":"us","owner":"data-platform","notes":"smoke test"}'
echo

echo "Register ETL source:"
curl -s -X POST "${BASE_URL}/v1/etl/sources" \
  -H "Content-Type: application/json" \
  -d '{"sourceId":"src_demo_finance","name":"Demo Finance Source","systemType":"warehouse","domain":"finance","connectionMode":"db","owner":"data-platform","metadata":{"env":"demo"}}'
echo

echo "Record ETL run:"
curl -s -X POST "${BASE_URL}/v1/etl/runs" \
  -H "Content-Type: application/json" \
  -d '{"sourceId":"src_demo_finance","recordsExtracted":2500,"recordsLoaded":2498,"status":"success","qualityScore":0.95,"lineageCoverage":0.96,"notes":"daily load"}'
echo

echo "Run reverse security scenario:"
curl -s -X POST "${BASE_URL}/v1/playground/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"reverse","domain":"security","scenarioId":"sec-vuln-critical","actor":"demo-user","dryRun":true}'
echo
