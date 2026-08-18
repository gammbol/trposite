# Test cluster

The project uses several complementary testing methodologies instead of relying
on one unit-test suite.

## Methodologies

- **Unit tests** isolate normalization, symbolic verification, domain checks,
  scoring, consensus grouping and ranking.
- **Integration tests** exercise Django REST API contracts without calling real
  LLM providers.
- **Differential tests** compare several independent candidate solutions and
  verify that mathematical validity has priority over majority voting.
- **Property-based tests** generate families of ODEs and verify invariants over
  many automatically generated coefficients.
- **Fuzz tests** send malformed/random mathematical and LLM payloads to parser
  boundaries and ensure failures remain controlled.
- **Resilience/fault-injection tests** simulate missing API keys, unavailable
  providers, timeouts, malformed model output and exhausted self-correction.
- **Regression tests** pin known edge cases such as arbitrary-constant renaming,
  second-order generality and invalid consensus candidates.
- **Load probe** measures latency, throughput and failure rate of the fast SymPy
  endpoint separately from slow AI providers.

## Install test dependencies

```bash
cd backend
python -m pip install -r requirements-test.txt
cd ..
```

## Run complete automated cluster

```bash
./scripts/run_test_cluster.sh
```

Artifacts are written to `.pytest_cache/reports/` (already ignored by Git):

- `junit.xml` — machine-readable test results;
- `coverage.xml` — coverage report for backend applications.

## Run a single methodology

```bash
pytest tests/unit
pytest tests/integration
pytest tests/differential
pytest tests/property
pytest tests/fuzz
pytest tests/resilience
pytest tests/regression
```

## Run load probe

Start Django first:

```bash
cd backend
python manage.py runserver
```

Then from another terminal:

```bash
python tests/load/load_solve.py --requests 200 --workers 20
```

The load probe intentionally targets `/api/solve/` because that is the
latency-sensitive deterministic path. LLM latency is evaluated separately and
must not distort the normal user response-time metric.
