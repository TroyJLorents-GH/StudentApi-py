---
project: projects/StudentApi-py
type: readme
---

# Student Hiring System API (SAMS) — Python / FastAPI

![Azure](https://img.shields.io/badge/hosted%20on-Azure_App_Service-blue)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688?logo=fastapi)
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy_2.0-red)

The **FastAPI backend** for SAMS (Student Assignment Management System), the student-hiring
platform for ASU's School of Computing and Augmented Intelligence (SCAI). It powers student
and class lookups, TA/IA/Grader assignment workflows, compensation and cost-center
calculation, bulk uploads, analytics dashboards, role-based access control (RBAC), an
admin user-management console with audit logging, and an LLM-backed support chatbot (IRA).

> **This repository is the portfolio replica** of an internal ASU system. It mirrors the
> production backend but with two intentional differences: no ASU CAS single sign-on
> (replaced by cookie-based fake-user impersonation so reviewers can experience each RBAC
> role), and no real student PII / real cost-center numbers. See
> `docs/superpowers/specs/2026-06-23-replica-sync-portfolio-rbac-design.md`.

---

## Live Demo

* **API docs (Swagger UI):** https://studenthiringapp-d8cxb6h0e8eyevhf.westus-01.azurewebsites.net/docs
* **Frontend (React):** https://blue-moss-0cf2b2f10.1.azurestaticapps.net/

The React frontend lives in a separate repository (`ui-student-py`).

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Prerequisites](#prerequisites)
7. [Getting Started](#getting-started)
8. [Configuration / Environment](#configuration--environment)
9. [Authentication & RBAC](#authentication--rbac)
10. [API Reference](#api-reference)
11. [Domain Logic](#domain-logic)
12. [Deployment & CI/CD](#deployment--cicd)
13. [Notes & Caveats](#notes--caveats)
14. [License](#license)

---

## Overview

SAMS manages the hiring of student employees (Teaching Assistants, Instructional Assistants,
and Graders) against class sections each academic term. The API:

* Looks up students (`StudentData` table) and class sections (per-term `ClassSchedule` tables).
* Creates, edits, and bulk-uploads **class assignments**, automatically computing
  **compensation** and a **cost-center key** from position, education level, session,
  campus, and academic career.
* Surfaces **analytics** (hiring trends, enrollment heatmaps, fill rates, offer pipeline,
  cost-per-enrolled, KPIs) across terms.
* Exposes **applications** submitted by Masters IA/Grader and PhD candidates.
* Enforces **role-based access control** via a `user_access` table and a permission engine.
* Provides an **admin console** for managing users and reviewing an audit log.
* Hosts **IRA**, a scoped support chatbot that proxies ASU's CreateAI gateway (Claude Opus)
  with read-only tool calling against SAMS data.

The database is **Azure SQL** (SQL Server) accessed through SQLAlchemy + pyodbc; the code
also supports local SQL Server Express via a trusted-auth ODBC connection string.

---

## Features

* **Student Lookup** — find a student by 10-digit ASU ID or ASUrite.
* **Class Schedule Browsing** — cascading subject → catalog → class-number → details lookups.
* **Assignment Management**
  * Create single assignments with auto-calculated compensation + cost center.
  * Bulk CSV/XLSX upload with a **Calibrate Preview** step that validates and enriches
    rows (student/class details) before commit.
  * Bulk-edit and soft-delete (versioned via the `Instructor_Edit` flag).
  * Per-student **summary** with per-session (A/B/C) weekly-hour totals.
  * Per-instructor **Manage Assignments** view + edit.
* **Applications** — Masters IA/Grader application submissions and PhD application
  submissions (term-scoped).
* **Analytics** — 25+ endpoints feeding charts: cross-term hiring trends, enrollment by
  subject/instructor/mode, fill rates, grader ratios, cost-per-enrolled, offer pipeline,
  and KPI cards.
* **RBAC** — roles (`admin`, `program_chair`, `faculty_grader`, `default`, plus `custom`)
  with per-feature permission flags, merged from role defaults and per-user overrides.
* **Admin Console** — create/update/delete users, list users with effective permissions,
  and an append-only **audit log** of admin actions.
* **IRA Chatbot** — LLM support agent (read-only tools: student lookup, class lookup,
  remaining hours, class assignments) gated behind the `chat` permission.
* **Offer-letter templates** — `.docx` templates for IA and Grader offer letters.
* **Health check** — `/healthz` plus an optional debug `/routes` listing.

---

## Architecture

```
                React frontend (ui-student-py, Azure Static Web Apps)
                                   │  (cookie `auth` = asurite, credentials included)
                                   ▼
        ┌───────────────────────────────────────────────────────────┐
        │                 FastAPI app (main.py)                      │
        │  SessionMiddleware · CORSMiddleware                        │
        │                                                            │
        │  Routers (routes/):                                        │
        │   auth · student · assignment · class_schedule ·          │
        │   application · manage_assignments · phd_application ·     │
        │   faculty · admin_users · analytics · chat                │
        │                                                            │
        │  dependencies.py  → current_user / require_perm (RBAC)     │
        │  utils/rbac.py    → ROLE_DEFAULTS + merged_perms           │
        │  utils/assignment_utils.py → compensation + cost center    │
        └───────────────────────────────────────────────────────────┘
              │ SQLAlchemy ORM (models/)            │ requests
              ▼                                     ▼
       Azure SQL / SQL Server              ASU CreateAI gateway
       (pyodbc, schema dbo)                (OpenAI-compatible, Claude Opus)
```

**Request flow.** The React app authenticates by hitting `/api/dev-impersonate?asurite=…`,
which sets an httpOnly `auth` cookie. Every protected route resolves the cookie to a
`user_access` row through `current_user`, computes effective permissions with
`merged_perms`, and `require_perm("flag")` returns 403 when the flag is not granted.

**Per-term tables.** Class schedules are stored in one table per term
(`ClassSchedule2254`, `ClassSchedule2261`, `ClassSchedule2264`). Analytics and chat resolve
the right model via a `TERM_MODELS` map and an `ACTIVE_TERM` env pin. Assignments live in a
single `StudentClassAssignments` table with a `Term` column.

**Versioned edits.** Assignments are never hard-deleted in the bulk flows. The
`Instructor_Edit` flag marks rows as edited (`Y`), deleted (`D`), or active
(`NULL`/`''`/`N`); "truly hired" queries filter on that flag.

---

## Tech Stack

See [`TECHSTACK.md`](TECHSTACK.md) for the full breakdown. In short: **FastAPI** on
**Uvicorn/Gunicorn**, **SQLAlchemy 2.0** ORM over **pyodbc** to **Azure SQL**, **Pydantic v2**
schemas, deployed to **Azure App Service** via **GitHub Actions**.

---

## Project Structure

```
StudentApi-py/
├── main.py                     # App entry: middleware, router registration, /healthz
├── database.py                 # SQLAlchemy engine/session; ODBC vs URL handling; get_db
├── dependencies.py             # current_user + require_perm (RBAC dependencies)
├── requirements.txt            # Pinned dependencies
├── .env                        # Local secrets (gitignored)
│
├── models/                     # SQLAlchemy ORM models
│   ├── student.py              #   StudentData (StudentLookup)
│   ├── assignment.py           #   StudentClassAssignments
│   ├── class_schedule.py       #   ClassSchedule2254 / 2261 / 2264 + ACTIVE_TERM
│   ├── application.py          #   Masters IA/Grader applications
│   ├── phd_application.py      #   PhD applications
│   ├── user_access.py          #   user_access (RBAC source of truth)
│   └── admin_audit_log.py      #   AdminAuditLog
│
├── routes/                     # FastAPI routers (one per feature area)
│   ├── auth.py                 #   /api/ping, /api/user, /api/dev-impersonate, /api/dev-logout
│   ├── student.py              #   /api/StudentLookup
│   ├── assignment.py           #   /api/StudentClassAssignment (CRUD, upload, preview, summary)
│   ├── class_schedule.py       #   /api/class (subjects/catalog/classnumbers/details)
│   ├── application.py          #   /api/MastersApplication
│   ├── phd_application.py      #   /api/PhdApplication
│   ├── manage_assignments.py   #   /api/manage-assignments
│   ├── faculty.py              #   /api/faculty
│   ├── admin_users.py          #   /api/admin (users + audit logs)
│   ├── analytics.py            #   /api/analytics (charts/KPIs)
│   └── chat.py                 #   /api/chat (IRA chatbot)
│
├── schemas/                    # Pydantic v2 DTOs (request/response models)
├── utils/
│   ├── rbac.py                 #   ROLE_DEFAULTS + merged_perms
│   ├── users.py
│   └── assignment_utils.py     #   compensation tables + cost-center rules
│
├── templates/offer_letters/    # IA + Grader offer-letter .docx templates
├── db/migrations/              # SQL migration(s) (SQL Server)
├── docs/superpowers/           # Design specs + implementation plan
└── .github/workflows/          # Azure App Service deploy pipelines
```

---

## Prerequisites

* [Python 3.11+](https://www.python.org/downloads/) (CI builds on 3.13)
* **ODBC Driver 17/18 for SQL Server** (required by `pyodbc`)
* A SQL Server database — Azure SQL or local SQL Server Express
* (Optional) [Azure CLI](https://learn.microsoft.com/cli/azure/) for deployment

---

## Getting Started

```bash
# 1. Clone
git clone <repo-url>
cd StudentApi-py

# 2. Create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate
# POSIX:    source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env (see Configuration below)

# 5. Run the dev server
uvicorn main:app --reload
```

Then browse to:

* Swagger UI → http://localhost:8000/docs
* ReDoc → http://localhost:8000/redoc
* Health → http://localhost:8000/healthz

> **Note:** there is no `alembic`/migration runner wired into the app — the database schema
> is applied manually. See `db/migrations/2026-06-23-replica-sync.sql` for the SQL Server
> DDL and seed used to bring a database in sync (run against both local and Azure DBs).

---

## Configuration / Environment

Configuration is read from a gitignored `.env` (loaded by `python-dotenv` in
`database.py`). In production these are set in **Azure App Service → Configuration**, which
overrides any committed values.

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | **Yes** | DB connection. Either a full SQLAlchemy URL (e.g. `mssql+pyodbc://…`) **or** a raw ODBC string starting with `Driver=` (auto URL-encoded as `mssql+pyodbc:///?odbc_connect=…`). App raises on startup if unset. |
| `ACTIVE_TERM` | Recommended | Term code (e.g. `2254`) that pins analytics, chat, and assignment routes to the same term. Defaults differ across modules (`2254`/`2264`), so set it explicitly. |
| `SESSION_SECRET` | Recommended | Secret key for Starlette `SessionMiddleware` (defaults to `dev-secret`). |
| `DEBUG_ROUTES` | No | `true` enables the `/routes` debug endpoint. |
| `CAS_ENABLED` | No | Carried for parity with the source system; CAS is disabled in this replica. |
| `ASU_AIML_TOKEN` (or `CREATEAI_API_KEY`) | For chat | Bearer token for the ASU CreateAI gateway. Chat returns 500 if missing. |
| `ASU_GATEWAY_BASE` (or `CREATEAI_BASE_URL`) | No | Gateway base URL. Default `https://api-main.aiml.asu.edu`. |
| `ASU_GATEWAY_MODEL` (or `CREATEAI_MODEL`) | No | Model id. Default `aws/claude4_8_opus`. |
| `ASU_AIML_PROJECT_ID`, `ASU_AIML_ENDPOINT` | No | Additional CreateAI metadata. |

Term-code convention: codes ending in `4` are **summer** terms (weekly-hour cap 40 and
simplified summer cost-center rules); otherwise the cap is 20.

---

## Authentication & RBAC

This replica uses **cookie-based dev impersonation** instead of CAS SSO:

1. `GET /api/dev-impersonate?asurite=<id>` sets an httpOnly `auth` cookie.
2. `current_user` (in `dependencies.py`) reads the cookie, loads the matching
   `user_access` row, and builds an effective-permissions dict via `merged_perms`.
3. `require_perm("flag")` is a dependency factory that 403s unless the user is an admin
   or holds the flag.

**Roles** (`utils/rbac.py` `ROLE_DEFAULTS`): `admin`, `program_chair`, `faculty_grader`,
`default`, and `custom` (no defaults — flags come purely from the row). Permission flags
include `assignment_adder`, `applications`, `phd_applications`, `student_summary_page`,
`bulk_upload_assignments`, `manage_assignments`, `master_dashboard`, `faculty_dashboard`,
`program_chair_uploads`, `faculty_quickassign`, `faculty_grader_uploads`, `analytics`,
`chat`, and `login`. Effective perms = role defaults overlaid with any boolean overrides
on the user row.

> The dev-impersonate endpoints are clearly marked **DEV ONLY**. Admins cannot modify or
> delete their own `user_access` row (guarded in `routes/admin_users.py`).

---

## API Reference

All paths are mounted under `/api` except the root and health endpoints. Browse the live
Swagger UI for full request/response schemas.

### Auth
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/ping` | Liveness (`pong`) |
| GET | `/api/dev-impersonate?asurite=` | DEV: set `auth` cookie |
| GET | `/api/user` | Current user + effective perms |
| GET | `/api/dev-logout` | DEV: clear `auth` cookie |

### Students & Classes
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/StudentLookup/{identifier}` | By 10-digit ID or ASUrite |
| GET | `/api/class/subjects?term=` | Distinct subjects |
| GET | `/api/class/catalog?term=&subject=` | Catalog numbers |
| GET | `/api/class/classnumbers?term=&subject=&catalogNum=` | Class numbers |
| GET | `/api/class/details/{classNum}?term=` | Full class details |

### Assignments
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/StudentClassAssignment/` | Active assignments |
| GET | `/api/StudentClassAssignment/admin` | All (admin only) |
| GET | `/api/StudentClassAssignment/my-uploads` | Filtered by `ImportedBy` |
| GET | `/api/StudentClassAssignment/totalhours/{student_id}` | Sum of active weekly hours |
| GET | `/api/StudentClassAssignment/student-summary/{identifier}` | Summary + per-session totals |
| GET | `/api/StudentClassAssignment/{assignment_id}` | Offer/status fields |
| POST | `/api/StudentClassAssignment/` | Create one |
| PUT | `/api/StudentClassAssignment/{assignment_id}` | Update fields |
| POST | `/api/StudentClassAssignment/bulk-edit` | Versioned bulk edit + soft delete |
| POST | `/api/StudentClassAssignment/upload` | Commit CSV/XLSX batch |
| POST | `/api/StudentClassAssignment/calibrate-preview` | Validate + enrich before commit |
| GET | `/api/StudentClassAssignment/template` | CSV upload template (5-col) |
| GET | `/api/StudentClassAssignment/template-legacy` | Legacy 12-col template |

### Applications
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/MastersApplication` | Masters IA/Grader applications |
| GET | `/api/PhdApplication?term=` | PhD applications (term-scoped) |

### Faculty / Manage
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/faculty/student-assignments` | Faculty dashboard (perm-gated) |
| GET | `/api/manage-assignments/by-instructor/{instructor_id}` | Instructor's assignments |
| PUT | `/api/manage-assignments/{assignment_id}` | Edit + recompute comp/cost center |

### Admin (admin role required)
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/admin/users` | List users + effective perms |
| POST | `/api/admin/users` | Create user |
| PATCH | `/api/admin/users/{asu_id}` | Update role/flags (audited) |
| DELETE | `/api/admin/users/{asu_id}` | Delete user (audited) |
| GET | `/api/admin/audit-logs?limit=` | Recent admin actions |

### Analytics (`analytics` perm) — `/api/analytics/...`
`trend`, `enrollment`, `hiring/by-term`, `hiring/compensation-by-term`,
`hiring/by-position`, `hiring/top-instructors`, `hiring/kpis`,
`enrollment/by-subject`, `enrollment/fill-rate-by-subject`,
`enrollment/top-instructors`, `enrollment/mode-mix`, `enrollment/kpis`,
`enrollment/course-by-term`, `enrollment/subjects`, `enrollment/instructors`,
`enrollment/catalogs`, `enrollment/course-by-instructor`,
`enrollment/instructor-load`, `enrollment/levels`,
`students/by-degree`, `students/by-org`, `students/by-plan`, `students/by-campus`,
`students/kpis`, `cross/grader-ratio-by-subject`,
`cross/cost-per-enrolled-by-subject`, `cross/offer-pipeline`.

### Chat
| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/chat` | IRA support chatbot (perm `chat`) |

### System
| Method | Path | Notes |
| --- | --- | --- |
| GET | `/` | Welcome message |
| GET | `/healthz` | `{ "ok": true }` |
| GET | `/routes` | Route list (only if `DEBUG_ROUTES=true`) |

---

## Domain Logic

**Compensation** (`utils/assignment_utils.calculate_compensation`) is a lookup over
discrete rate tables keyed by `(Position, EducationLevel, FultonFellow, WeeklyHours,
ClassSession)`. Positions: `TA`, `IA`, `Grader`, `TA (GSA) 1 credit`,
`TA (GSA) 1 credit +`. Session `C` (full term) pays double the half-session A/B rate for
hourly positions. Unmatched combinations return `0`.

**Cost-center key** (`compute_cost_center_key`) resolves a budget code (e.g.
`CC9002/PG90004`) from `(Position, Location, Campus, AcadCareer)`. Summer terms (code ends
in `4`) use a simplified rule set where academic career is ignored. Unmatched → `UNKNOWN`.

**Academic career** is inferred from catalog number (`infer_acad_career`): 100–499 → `UGRD`,
otherwise `GRAD`.

**Weekly-hour caps** (used by chat/availability): 40 for summer terms, 20 otherwise;
session C hours count against both A and B limits.

> Compensation figures and cost-center codes in this replica are **faked** for portfolio
> use and do not reflect real ASU pay rates or budget codes.

---

## Deployment & CI/CD

Deployed to **Azure App Service** (Linux, Python). Two GitHub Actions workflows live in
`.github/workflows/` (`main_studenthiringapp.yml`, `main_studenthiringapppy.yml`). On push
to `main`:

1. Checkout, set up Python 3.13, create a venv, `pip install -r requirements.txt`.
2. Upload the build artifact (Oryx performs the real build on Azure).
3. Authenticate to Azure via OIDC federated credentials and deploy with
   `azure/webapps-deploy@v3` to the `Production` slot.

Azure runs the app under Gunicorn/Uvicorn workers; `DATABASE_URL`, `ACTIVE_TERM`, and the
CreateAI secrets are set in App Service Configuration (not committed).

See [`SERVICES.md`](SERVICES.md) for the hosted services this project depends on.

---

## Notes & Caveats

* **No CAS in this replica.** Auth is cookie impersonation for portfolio demos; the
  production system uses ASU CAS SSO.
* **Route ordering matters.** In `routes/assignment.py`, static paths
  (`/calibrate-preview`, `/upload`, `/template`, `/student-summary/...`) are declared
  before the catch-all `/{assignment_id}` so they aren't shadowed.
* **SQL Server quirks** are worked around in `analytics.py` (e.g. grouping by raw columns
  instead of `CONCAT(...)` to avoid SQL Server error 8120; counting only `ClassType='E'` /
  `ClassStatus='A'` enrollment sections to avoid double-counting REC/LAB components).
* **CreateAI gateway quirk:** the gateway drops `role:"tool"` messages, so `chat.py` feeds
  tool results back as user-role `[TOOL RESULT ...]` messages (documented in the module).
* `requirements.txt` is UTF-16 encoded.
* The README's earlier reference to a `LICENSE` file remains, but no `LICENSE` file is
  currently present in the repo.

---

### Created by Troy Lorents

## License

Intended to be licensed under the MIT License. (No `LICENSE` file is currently committed.)
