# Timepiece

A scheduling and care management system for Swedish home care (hemtjänst). Admins plan shifts, assign care workers to customers, track visits, and monitor continuity. Employees view their own schedules, visits, and absences.

## Tech stack

**Backend:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Alembic, Pydantic v2, JWT auth, structlog

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query, React Router, Lucide icons

**Tools:** Python 3.13, uv, Bun, ruff, pyright, pre-commit

## Prerequisites

- [Python 3.13](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Bun](https://bun.sh/) — JavaScript runtime / package manager
- [PostgreSQL](https://www.postgresql.org/) — running locally or via Docker

## Setup

```bash
# Clone and enter
git clone <repo-url> && cd tp

# Backend
cp .example.env .env          # Edit with your database credentials
make install                  # Install Python deps + pre-commit hooks
make migrate                  # Run database migrations

# Frontend
cd frontend && bun install    # Install JS deps
```

### Create an admin user

There is no public registration — the first admin must be seeded. Create a `seed.py` in the project root:

```python
import asyncio, sys
sys.path.insert(0, "src")
from database import _get_database_session
from idp.email_and_password.repo import get_user_by_email, hash_password
from models import User

async def seed():
    db = _get_database_session()
    if await get_user_by_email(db, "admin@timepiece.se"):
        print("Already exists"); return
    db.add(User(email="admin@timepiece.se", hashed_password=hash_password("admin123"), is_admin=True, is_active=True))
    await db.commit()
    print("Created admin: admin@timepiece.se / admin123")
    await db.close()

asyncio.run(seed())
```

Then run:

```bash
uv run python seed.py
```

## Running

```bash
# Terminal 1 — backend (http://localhost:8000)
make run

# Terminal 2 — frontend (http://localhost:5173)
make frontend
```

The frontend proxies `/api` requests to the backend, so no CORS issues during development.

## Commands

| Command | Description |
|---------|-------------|
| `make run` | Start backend dev server on :8000 |
| `make frontend` | Start frontend dev server on :5173 |
| `make install` | Install deps + pre-commit hooks |
| `make test` | Run pytest |
| `make coverage` | Run tests with coverage report |
| `make lint` | Run ruff + pyright |
| `make migrate` | Run Alembic migrations |
| `make downgrade` | Rollback one migration |

## Environment variables

See `.example.env` for all available options:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) | — |
| `TEST_DATABASE_URL` | Test database connection string | — |
| `SECRET_JWT_SIGNING_KEY` | JWT signing secret (min 16 chars) | — |
| `JWT_EXPIRATION_TIME_IN_HOURS` | Token lifetime | `24` |
| `CORS_ORIGINS` | Allowed origins (JSON array) | `["http://localhost:5173"]` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_AS_JSON` | JSON-formatted logs | `false` |

## API documentation

With the backend running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Project structure

```
tp/
├── src/                    # Backend
│   ├── api.py              # FastAPI app, middleware, router assembly
│   ├── config.py           # Pydantic settings
│   ├── database.py         # Async SQLAlchemy engine + session
│   ├── models.py           # All ORM models
│   ├── dependencies.py     # Shared FastAPI dependencies
│   ├── idp/                # Auth (login, JWT, cookies)
│   ├── employees/          # Employee CRUD
│   ├── customers/          # Customer CRUD
│   ├── measures/           # Care task definitions
│   ├── schedules/          # Shift planning + assignments
│   ├── care_visits/        # Visit tracking + status
│   ├── absences/           # Absence registration
│   ├── reports/            # Analytics endpoints
│   ├── permissions/        # RBAC system
│   └── audit/              # Immutable mutation log
├── frontend/               # Frontend
│   ├── src/
│   │   ├── api/            # API client
│   │   ├── components/     # Sidebar, shared components
│   │   ├── hooks/          # useAuth, custom hooks
│   │   ├── layouts/        # AppLayout (auth guard + sidebar)
│   │   └── pages/          # Login, Dashboard, Employees, etc.
│   ├── index.html
│   └── vite.config.ts
├── alembic/                # Database migrations
├── tests/                  # Backend tests
├── Makefile
└── pyproject.toml
```
