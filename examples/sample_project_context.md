# Sample Project Context — PAIOS-Lite Demo Fixture

This file is the demo fixture for the Memory Agent. It simulates the context
of a real project so the agent can produce a meaningful continuity brief
without needing a full directory scan.

---

## Project: task-tracker-api

A REST API for tracking personal tasks, built with FastAPI and PostgreSQL.
The project is in active early development. The core CRUD layer is complete;
authentication is partially implemented and currently blocking progress.

### Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x
- **Database**: PostgreSQL 16 (Docker Compose for local dev)
- **Auth**: JWT in HttpOnly cookies (chosen for XSS protection)
- **Tests**: pytest, httpx for async test client

---

## Current Status

| Area | Status |
|---|---|
| Task CRUD endpoints (`/tasks`) | Done |
| User registration (`/auth/register`) | Done |
| Login + JWT issuance (`/auth/login`) | Done |
| Token refresh (`/auth/refresh`) | Not started |
| JWT validation middleware | In progress — happy path works, edge cases failing |
| DB connection pooling | Blocked — pool size config not finalized |
| Rate limiting | Not started |
| Integration test suite | Not started |
| Deployment pipeline | Not started |

---

## Recent Decisions

- Chose FastAPI over Flask for native async support and auto-generated OpenAPI docs.
- JWT refresh tokens stored in the database (not stateless) to support revocation.
- Docker Compose chosen for local development; Fly.io shortlisted for production.
- Decided NOT to use an ORM migration tool yet — raw `CREATE TABLE` for now,
  will add Alembic before first deployment.

---

## Open Items

- TODO: Implement `/auth/refresh` endpoint (blocked by token storage schema)
- TODO: Add integration tests for the full auth flow
- TODO: Finalize DB connection pool settings (see issue #12)
- TODO: Add rate limiting middleware before going public
- FIXME: `GET /tasks/{id}` returns HTTP 500 on missing task instead of 404
- FIXME: JWT middleware does not handle expired tokens gracefully — raises
  unhandled exception instead of returning 401

---

## Key Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app factory, router registration |
| `auth/jwt.py` | JWT creation and validation (partially complete) |
| `auth/middleware.py` | JWT validation middleware (in progress) |
| `db/session.py` | SQLAlchemy async session factory |
| `routers/tasks.py` | Task CRUD endpoints (complete) |
| `routers/auth.py` | Auth endpoints (register + login done, refresh missing) |
| `models/task.py` | SQLAlchemy Task model |
| `models/user.py` | SQLAlchemy User model |
| `tests/` | Only scaffold tests exist — no integration tests yet |

---

## Continuity Notes

The auth flow should follow this sequence when complete:

1. `POST /auth/register` → creates user, returns 201
2. `POST /auth/login` → returns access token + refresh token (HttpOnly cookies)
3. `GET /tasks` → requires valid access token in cookie
4. `POST /auth/refresh` → exchanges refresh token for new access token

**Current blocker**: The refresh token table schema is undefined. Unblock this
first, then the `/auth/refresh` endpoint can be built.

**Next recommended action**: Define the `refresh_tokens` table in `db/schema.sql`,
add the SQLAlchemy model, then implement the endpoint.
