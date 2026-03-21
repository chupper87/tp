# op-schema Reference

op-schema (internally "Timepiece") was a scheduling and care management app for Swedish elderly home care (hemtjänst) that was built but never finished. **tp is a fresh rewrite of the same domain.**

Source: op-schema repository (archived, not actively maintained)

---

## Domain model

### User
- Email + password authentication
- Invite-by-email system (user receives link, sets password)
- Roles: `ADMIN`, `EMPLOYEE`, `ASSISTANT_NURSE`, `CARE_ASSISTANT`, `USER`

### Employee (care worker)
- Fields: name, role (RoleType), employment_type, employment_rate (%), phone, address
- Linked to User for login
- Has absences (sick, VAB, vacation, parental leave, leave of absence)
- Assigned to schedules

### Customer (care recipient)
- Fields: name, care_level (HIGH/MEDIUM/LOW), approved_hours_per_week, address, key_code, phone, notes
- Soft delete via `is_active`
- Has CustomerMeasures (approved care tasks)
- Assigned to schedules

### Measure (care task)
- Fields: name, description, standard_duration_minutes, frequency (DAILY/WEEKLY/MONTHLY), time_of_day (MORNING/EVENING/FLEXIBLE)
- Examples: "Shower", "Breakfast", "Medication", "Mobility training"
- Each customer has a subset of approved measures (CustomerMeasure junction table)

### Schedule
- One schedule per date + shift (MORNING/DAY/EVENING/NIGHT)
- Has assigned employees (ScheduleEmployee)
- Has assigned customers (ScheduleCustomer)
- Has scheduled measures per customer (ScheduleMeasure)
- Can be archived (ScheduleArchive) — JSONB snapshot for history

### CareVisit
- One visit = one employee visiting one customer
- Status: PLANNED → COMPLETED / CANCELLED / NO_SHOW / LATE / PARTIAL
- Linked to schedule, employee, customer
- Indexed on (employee_id, date), (customer_id, date), (schedule_id)

### Absence
- Employee absence record
- Types: SICK, VAB, VACATION, PARENTAL_LEAVE, LEAVE_OF_ABSENCE
- Date range (start_date, end_date)
- Indexed on (employee_id, start_date, end_date)

---

## What worked well — keep in tp

- Clean layer separation: models / schemas / repo (crud) / api (routers)
- PostgreSQL + async SQLAlchemy with `Mapped[]` types
- Alembic for migrations
- JWT auth (HTTPOnly cookie)
- RBAC with role enum on Employee
- Composite indexes on (date, status), (customer_id, date), etc.
- Soft delete (`is_active`) for customers
- `ScheduleArchive` for historical snapshots (JSONB data)
- bcrypt for passwords
- FastAPI + Pydantic for validation
- uv as package manager
- ruff + pyright + pre-commit

---

## What failed / was missing — avoid in tp

| Failure | Fix in tp |
|---------|-----------|
| Frontend never connected to backend — all mock data | Connect frontend from day one, no hardcoded data |
| No create/edit forms built | Build CRUD UI for every entity before moving on |
| dnd-kit imported but never implemented | Only add drag-and-drop when the basic schedule flow works |
| Statistics page left empty | Define reports as API endpoints first, then build UI |
| No error handling or loading states in frontend | Enforce error boundary + loading state pattern from start |
| No frontend tests | Write component tests alongside features |
| No audit logging | Plan AuditTrail model early |
| No Docker setup | Add docker-compose before going to production |
| No bulk operations in API | Add bulk endpoints where needed (e.g. assign multiple employees) |
| No schedule conflict detection | Build conflict check into schedule assignment logic |

---

## Feature backlog

### MVP (must have before any real use)
- [ ] Employee CRUD with absence management
- [ ] Customer CRUD with care level + approved hours
- [ ] Measure library (care task definitions)
- [ ] Schedule creation: date + shift + assign employees + customers
- [ ] CareVisit tracking with status transitions
- [ ] Frontend connected to API — no mock data
- [ ] Forms for all entities

### Medium priority
- [ ] Schedule conflict detection (double-booking, absence overlap)
- [ ] Reports: worked hours per employee, completed visits per customer
- [ ] Audit logging (who changed what, when)
- [ ] Password reset via email
- [ ] Role-based UI visibility

### Lower priority
- [ ] Docker containerization
- [ ] Drag-and-drop schedule UI (dnd-kit)
- [ ] Real-time updates (WebSockets)
- [ ] Notifications on schedule changes
- [ ] Mobile app

---

## op-schema tech stack (reference only)

Backend: FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT, bcrypt, FastAPI-Mail, Loguru, pytest, uv
Frontend: React 19, TypeScript, Vite, Tailwind CSS, React Query, React Router, dnd-kit, Axios

tp uses the same backend stack except: structlog instead of Loguru, async SQLAlchemy from the start, and UUID primary keys.
