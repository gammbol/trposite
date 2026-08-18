#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p .pytest_cache/reports

python -m pytest \
  tests/unit \
  tests/differential \
  tests/property \
  tests/fuzz \
  tests/integration \
  tests/resilience \
  tests/regression \
  --cov=solver \
  --cov=history \
  --cov-report=term-missing \
  --cov-report=xml:.pytest_cache/reports/coverage.xml \
  --junitxml=.pytest_cache/reports/junit.xml
