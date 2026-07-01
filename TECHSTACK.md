---
project: projects/StudentApi-py
type: techstack
---

# Tech Stack — StudentApi-py (SAMS API)

The FastAPI backend for SAMS (Student Assignment Management System). This document
breaks down the languages, frameworks, libraries, build/deploy tooling, and external
APIs the project depends on. Versions are taken from `requirements.txt` (pinned).

---

## Language & Runtime

| | |
| --- | --- |
| **Language** | Python 3.11+ (CI builds and deploys on Python **3.13**) |
| **Runtime model** | ASGI web application |
| **Dev server** | Uvicorn (`uvicorn main:app --reload`) |
| **Prod server** | Gunicorn with Uvicorn workers on Azure App Service |

---

## Web Framework

| Library | Version | Purpose |
| --- | --- | --- |
| **FastAPI** | 0.115.14 | Core web framework. Provides the `APIRouter` per feature area (`routes/`), dependency injection (`Depends`) for DB sessions and RBAC, and auto-generated OpenAPI/Swagger docs at `/docs` and `/redoc`. |
| **Starlette** | (via FastAPI) | Underlying ASGI toolkit. Used directly for `SessionMiddleware` (cookie-based dev auth) in `main.py`; FastAPI's `CORSMiddleware` is also wired here. |
| **Uvicorn** | 0.34.3 | ASGI server for local development. |
| **Gunicorn** | 23.0.0 | Production process manager (runs Uvicorn workers on Azure). |
| **anyio** / **sniffio** / **h11** | 4.9.0 / 1.3.1 / 0.16.0 | Async I/O and HTTP/1.1 plumbing pulled in by Starlette/Uvicorn. |
| **python-multipart** | 0.0.20 | Parses `multipart/form-data` for file uploads (CSV/XLSX assignment batch upload endpoints). |

---

## Data & ORM

| Library | Version | Purpose |
| --- | --- | --- |
| **SQLAlchemy** | 2.0.41 | ORM and engine. Models live in `models/`; `database.py` builds the engine and `get_db` session dependency. Uses the 2.0-style `declarative_base` and `future=True` engine. |
| **pyodbc** | 5.2.0 | ODBC driver bridge SQLAlchemy uses to talk to SQL Server / Azure SQL (`mssql+pyodbc`). Requires a system **ODBC Driver 17/18 for SQL Server**. |
| **greenlet** | 3.2.3 | Required by SQLAlchemy for its async/greenlet execution support. |

`database.py` accepts either a full SQLAlchemy URL in `DATABASE_URL` or a raw ODBC
connection string (auto URL-encoded as `mssql+pyodbc:///?odbc_connect=...`).

---

## Validation & Schemas

| Library | Version | Purpose |
| --- | --- | --- |
| **Pydantic** | 2.11.7 | Request/response DTOs (`schemas/`) and the chat request models. Pydantic v2. |
| **pydantic_core** | 2.33.2 | Rust-backed validation core for Pydantic v2. |
| **annotated-types** | 0.7.0 | Constraint metadata used by Pydantic. |
| **typing_extensions** / **typing-inspection** | 4.14.0 / 0.4.1 | Typing back-ports/inspection used by Pydantic and FastAPI. |

---

## HTTP Client & LLM Integration

| Library | Version | Purpose |
| --- | --- | --- |
| **requests** | unpinned | Synchronous HTTP client. Used in `routes/chat.py` to call the managed AI gateway's OpenAI-compatible `/v1/chat/completions` endpoint with tool calling. |
| **idna** | 3.10 | Internationalized domain name handling (a `requests`/`urllib3` dependency). |

---

## Configuration & Utilities

| Library | Version | Purpose |
| --- | --- | --- |
| **python-dotenv** | 1.1.1 | Loads `.env` into the environment in `database.py` (`load_dotenv()`). |
| **click** | 8.2.1 | CLI plumbing pulled in by Uvicorn/Gunicorn. |
| **colorama** | 0.4.6 | Cross-platform terminal colors (Uvicorn logging on Windows). |

---

## Standard Library (notable usage)

* **`csv`** + **`io`** — CSV upload parsing and template generation in `routes/assignment.py`.
  (No `pandas`/`openpyxl` dependency: bulk upload parsing is done with the stdlib `csv` module.)
* **`urllib`** — ODBC connection-string URL-encoding in `database.py`.
* **`re`**, **`json`**, **`datetime`** — used across `routes/chat.py` (action-token parsing,
  tool-call serialization, timestamps).

---

## Static Assets

* **`templates/offer_letters/`** — `ia_template.docx` and `grader_template.docx`, static
  Microsoft Word offer-letter templates shipped with the repo (consumed by the offer-letter
  workflow; no server-side `python-docx` rendering dependency is present).

---

## Build, Tooling & Deployment

| Tool | Purpose |
| --- | --- |
| **pip** + `requirements.txt` | Dependency management (pinned versions; file is UTF-16 encoded). No `pyproject.toml`/Poetry. |
| **GitHub Actions** | CI/CD. Two workflows in `.github/workflows/` (`main_studenthiringapp.yml`, `main_studenthiringapppy.yml`) build on Python 3.13 and deploy to Azure App Service on push to `main`. |
| **Azure OIDC (federated credentials)** | `azure/login@v2` authenticates the deploy job without stored secrets; `azure/webapps-deploy@v3` pushes to the `Production` slot. |
| **Oryx** | Azure App Service's build system performs the real install/build on the platform after the artifact upload. |
| **venv** | Local virtual environments (`venv/` / `.venv/`). |

There is **no** Alembic / migration runner wired into the app. Schema changes are applied
manually via SQL in `db/migrations/` (SQL Server DDL).

---

## External APIs

| API | Used by | Notes |
| --- | --- | --- |
| **Managed AI gateway** | `routes/chat.py` | OpenAI-compatible `/v1/chat/completions` endpoint proxying **Claude Opus 4.8** (`aws/claude4_8_opus`). Authenticated with a single Bearer token (`CREATEAI_API_KEY`). Base URL configured via `CREATEAI_BASE_URL`. The gateway drops `role:"tool"` messages, so tool results are fed back as user-role `[TOOL RESULT ...]` text. |

See [`SERVICES.md`](SERVICES.md) for hosted-service details.
