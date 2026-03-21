# tp — Claude Code Project Guide

tp is a rewrite of **op-schema**, a Swedish home care (hemtjänst) scheduling system that was never finished. The goal is to build it right this time — professional architecture, real frontend connected to backend from day one, and clean domain logic.

See detailed reference in `.claude/op-schema-reference.md` — domain knowledge, what worked, what failed, feature backlog.

---

## Language

All code, docstrings, comments, and commit messages must be in **English**. No Swedish in code.

---

## Dependencies

Always use `uv add <package>` to add dependencies. Never edit `pyproject.toml` dependency lists manually.

---

## Commits

Commit incrementally as logical chunks are completed. Never accumulate a large uncommitted diff. Do **not** include `Co-Authored-By` lines in commit messages.

---

## Project domain

Swedish home care scheduling. Core entities:

| Entity | Description |
|--------|-------------|
| `User` | Authentication identity (email + password, JWT) |
| `Employee` | Care worker — role, employment type, absences |
| `Customer` | Care recipient — care level, approved hours, address, key code |
| `Measure` | Care task, e.g. "Shower", "Breakfast" — standard duration, frequency |
| `Schedule` | A work day/shift: date + shift type + assigned employees + customers |
| `CareVisit` | One visit: employee → customer, with status (planned/completed/cancelled…) |
| `Absence` | Employee absence: sick leave, VAB, vacation, parental leave, etc. |
| `ScheduleArchive` | JSONB snapshot of a finalized schedule for historical audit |

---

## Tech stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Web framework | FastAPI | Async-native, typed |
| ORM | SQLAlchemy 2.0 async | Mapped types, AsyncAttrs |
| DB driver | asyncpg | Async PostgreSQL |
| Migrations | Alembic (async) | Schema versioning |
| Validation | Pydantic v2 | Request/response schemas |
| Config | Pydantic BaseSettings | Typed env vars, SecretStr |
| Logging | structlog | JSON output, correlation IDs |
| Auth | JWT in HTTPOnly cookie | No SSO needed for hemtjänst |
| Passwords | bcrypt | Standard, safe |
| Package mgr | uv | Fast, lock-file based |
| Linting | ruff + pyright | Via pre-commit |

---

## Architecture patterns

Follow these patterns consistently:

### Enums
Use `StrEnum` + SQLAlchemy `String` column. Never use `sa.Enum(MyEnum)` — it creates a PostgreSQL ENUM type that is painful to migrate.

```python
class VisitStatus(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"

status: Mapped[Literal["planned", "completed"]] = mapped_column(String, ...)
```

### Error handling
Use the declarative `@api_exception_handler` decorator. Never raise `HTTPException` directly in routers.

```python
@api_exception_handler(EmployeeNotFound, status.HTTP_404_NOT_FOUND)
class EmployeeNotFoundError(ApiError):
    @classmethod
    def from_original_error(cls, e: EmployeeNotFound) -> "EmployeeNotFoundError":
        return cls(detail=f"Employee {e.employee_id} not found")
```

### Module structure
Each domain module follows this layout:

```
employees/
  __init__.py       # creates router, includes sub-routers
  repo.py           # DB queries only (async functions taking db: AsyncSession)
  schemas.py        # Pydantic in/out models
  errors.py         # domain exception classes
  admin_api.py      # admin-only endpoints
  public_api.py     # user-facing endpoints
```

Never put admin and user endpoints in the same router file.

### Dependencies
Use `src/dependencies.py` as the single import point for shared dependencies:
- `get_db` — AsyncSession
- `get_authenticated_user` — current User (401 if not logged in)
- `get_authenticated_admin_user` — admin User (403 if not admin)
- `get_model_by_id_or_404(Model)` — factory for ID lookup dependencies

### Logging
Use per-module loggers. Bind context at request start.

```python
log = get_logger(__name__)
log.info("created_employee", employee_id=str(employee.id))
```

### Primary keys
All models use UUID v4 via the `primary_key()` helper in `models.py`. Never use integer PKs.

### DateTime
Always use `DateTime(timezone=True)` with `server_default=func.now()`. Never store naive datetimes.

---

## What to avoid

- Raising `HTTPException` directly in route handlers — use the error framework
- Mixing admin and user endpoints in one file
- Integer primary keys
- SQLAlchemy `Enum` type (use `StrEnum` + `String`)
- Synchronous DB calls in async handlers
- Committing large diffs — commit per logical unit
- Hardcoded mock data anywhere — frontend must connect to real API from day one
- Audit trail missing — log who changed what (future: AuditTrail model)
- Schedule conflict detection missing (double-booking, absence overlap) — build this in

---

## Running the project

```bash
make install      # uv sync + pre-commit install
make run          # uvicorn dev server on :8000
make test         # pytest
make lint         # ruff + pyright
make migrate      # alembic upgrade head
make postgres     # docker compose database
```

---

## Module roadmap (MVP order)

1. `employees/` — CRUD, role management, absence tracking
2. `customers/` — CRUD, care level, approved hours
3. `measures/` — care task definitions with duration/frequency
4. `schedules/` — schedule creation, employee/customer assignment
5. `care_visits/` — visit tracking, status transitions
6. `absences/` — absence registration, overlap detection
7. `reports/` — worked hours, completed visits
