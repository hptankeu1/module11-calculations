# Module 11 – Calculation Model, Pydantic Validation & Factory Pattern

[![CI/CD](https://github.com/hptankeu1/module11-calculations/actions/workflows/ci.yml/badge.svg)](https://github.com/hptankeu1/module11-calculations/actions/workflows/ci.yml)

**Docker Hub:** https://hub.docker.com/r/htankeu/module11-calculations

```bash
docker pull htankeu/module11-calculations:latest
```

This module adds a `Calculation` data layer to the FastAPI + SQLAlchemy app from Module 10:
a SQLAlchemy model, Pydantic schemas with validation, a factory for the arithmetic logic,
and unit + integration tests that run in GitHub Actions against PostgreSQL. The BREAD
endpoints come in Module 12.

## Project layout

```
app/
├── database.py            # engine, SessionLocal, Base, get_db()
├── models/
│   ├── user.py            # User (Module 10)
│   └── calculation.py     # Calculation model (FK → users.id)
├── schemas/
│   ├── user.py            # UserCreate / UserRead
│   └── calculation.py     # CalculationType enum, CalculationCreate / CalculationRead
├── operations/
│   ├── __init__.py        # add / subtract / multiply / divide
│   └── factory.py         # Operation strategies + CalculationFactory
├── crud.py                # create/get/list helpers (used by Module 12 routes)
├── security.py            # bcrypt hashing
└── main.py                # FastAPI app (/health, /calculation-types)
tests/
├── unit/                  # no database needed
└── integration/           # real PostgreSQL
```

## Design decisions

| Topic | Choice |
|---|---|
| **Fields** | `id`, `user_id`, `a`, `b`, `type`, `result`, `created_at` |
| **Result** | **Stored**, computed once by the factory on creation. Calculations are history records, so storing keeps reads cheap and lets us sort/filter by result. `recompute()` refreshes it after an edit. |
| **user_id** | `ForeignKey("users.id", ondelete="CASCADE")`, `NOT NULL`, indexed. Deleting a user deletes their calculations, enforced by Postgres itself. |
| **type** | Python `CalculationType` enum (`Add`, `Sub`, `Multiply`, `Divide`) mapped to a native Postgres enum, so invalid values are rejected even by raw SQL. |
| **Validation layers** | 1) Pydantic `CalculationCreate` (API boundary) → 2) SQLAlchemy `@validates` on the model → 3) DB constraints (enum, NOT NULL, FK). |

### Validation in `CalculationCreate`
- `type` must be one of the four types (case-insensitive: `"add"` → `Add`)
- `a` and `b` must be finite numbers: rejects `NaN`, `±inf`, booleans, `None`, and non-numeric strings
- `Divide` with `b == 0` is rejected
- Extra fields (e.g. a client-supplied `result`) are rejected (`extra="forbid"`)

`CalculationRead` returns `id, user_id, a, b, type, result, created_at`. `UserRead` never exposes the password hash.

### Factory pattern
```python
from app.operations.factory import CalculationFactory

CalculationFactory.create("Divide")          # -> <DivideOperation '/'>
CalculationFactory.compute("Multiply", 6, 3) # -> 18
```
Each operation is a subclass of `Operation`. To add a new type (e.g. `Power`), add an enum
value, write one class and call `CalculationFactory.register(...)`. No existing code changes.

## Running the tests locally

The integration tests need PostgreSQL. Pick one option:

**Option A: Docker Compose (easiest)**
```bash
docker compose up -d db              # starts Postgres and creates calc_db + calc_test
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                               # all tests
```

**Option B: your own Postgres**
```bash
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/calc_test
pytest
```

Useful commands:
```bash
pytest tests/unit -v                 # unit tests only (no DB needed)
pytest tests/integration -v          # integration tests (PostgreSQL)
pytest --cov=app --cov-report=term-missing
```

Each integration test runs inside a transaction that is rolled back afterwards, so tests
are isolated and leave the database clean.

## Running the app

```bash
docker compose up --build
curl http://localhost:8000/health    # {"status":"ok","database":"connected"}
```
Or from Docker Hub:
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:5432/DBNAME \
  htankeu/module11-calculations:latest
```
Interactive docs: http://localhost:8000/docs

## CI/CD pipeline (`.github/workflows/ci.yml`)

1. **test**: starts a `postgres:16` service container and runs unit tests, integration tests, then the full suite with coverage (fails under 90%).
2. **security**: builds the image and scans it with Trivy (fails on fixable HIGH/CRITICAL).
3. **deploy**: on pushes to `main` only, pushes `latest` and the commit SHA tag to Docker Hub.

Required repository secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` (a Docker Hub access token).

## Screenshots

| | |
|---|---|
| Successful GitHub Actions run | ![Actions](docs/screenshots/github-actions.png) |
| Image on Docker Hub | ![Docker Hub](docs/screenshots/dockerhub.png) |

See [REFLECTION.md](REFLECTION.md) for the reflection.
