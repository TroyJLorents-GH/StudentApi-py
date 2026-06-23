# Replica Sync + Portfolio RBAC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the portfolio replica `StudentApi-py` + `ui-student-py` up to parity with source `StudentApi-asu` (analytics, read-only chatbot, schema/comp columns, RBAC flags) and add a 3-fake-user role-picker login so portfolio viewers can experience RBAC from each role — without CAS and without real data.

**Architecture:** Port new source features into the replica, adapting for two structural differences: (1) source uses one stacked `ClassSchedule` table while replica uses per-term tables `ClassSchedule2254/2261/2264`; (2) replica uses dev-impersonate cookie auth, no CAS. Real ASU financial values are scrubbed to fakes. DB schema changes apply to BOTH local `samsdb` and Azure `MyStudentDb_v2`.

**Tech Stack:** FastAPI, SQLAlchemy, SQL Server / Azure SQL (pyodbc), React (CRA), MUI X Charts.

## Global Constraints

- DB schema changes MUST be applied to BOTH `samsdb` (local, `Troyjl\SQLEXPRESS`) AND Azure `MyStudentDb_v2`. Run each DDL block in SSMS against both.
- Source repos `StudentApi-asu` / `py-student-ui-asu` are READ-ONLY reference. Never modify them.
- No CAS. Keep `REACT_APP_USE_CAS=false`. No CAS code runs in the replica.
- No real student PII. All seed data is fake.
- SCRUB all real ASU values to fakes: cost-center codes `DR07557`, `DR08243`, `CC1139/PG08491`, `CC1139/PG08524`, all `CC0136/PG#####`, and pay rates `15.62`, `22.00`. Use the fake map in Task 4.2 consistently everywhere.
- Secrets (`CREATEAI_API_KEY`, DB password) live only in Azure App Service → Configuration and local `.env` — never committed.
- Chatbot is READ-ONLY: do NOT port the `create_assignment` write tool.
- Comp summer-cap: add columns only; do NOT port the session-aware `get_total_hours`/cap-enforcement rewrite.
- Each task ends with a commit. Work on branch `feat/replica-sync-portfolio-rbac` (already created).

## Decisions captured (from brainstorming)

| Decision | Choice |
|---|---|
| Auth | Option A: 3 fake users + role-picker, dev-impersonate, no CAS |
| AdminAuditLog | Create `dbo.AdminAuditLog` (model exists, table name mismatch) |
| Features synced | Analytics, RBAC flags, Schema/comp cols, Chatbot (read-only) |
| Offer-letter | EXCLUDED (pywin32 Word COM, breaks on Azure Linux) |
| Chat LLM | ASU CreateAI gateway (`CREATEAI_*` env in Azure config) |
| Comp cap | Skip — columns only |
| Chat writes | Read-only — drop write tool |
| Scrub | Scrub all real cost-centers + pay rates to fake |

## File map

**Backend (`StudentApi-py`)**
- Modify `models/user_access.py` — +`analytics`,`chat` columns
- Modify `models/class_schedule.py` — define `ClassSchedule2261`,`ClassSchedule2264`; +`ClassType`,`ClassStatus`,`AssocClassNum` on all three
- Modify `models/assignment.py` — +4 cols + `Offer_Signed_Workday`
- Modify `models/student.py` — +4 cols
- Modify `dependencies.py` — +`require_perm` factory, +`analytics`/`chat` flags
- Modify `utils/rbac.py` — +`analytics`/`chat` in ROLE_DEFAULTS
- Modify `utils/users.py` — +`analytics`/`chat` flags
- Modify `utils/assignment_utils.py` — `calculate_compensation(a, term=None)`; SCRUB values
- Modify `routes/assignment.py` — +`VALID_POSITIONS`/`normalize_position`; pass `term=` at call sites
- Create `routes/analytics.py` — ported, term-table adapted
- Create `routes/chat.py` — ported, read-only, remapped
- Modify `main.py` — register `analytics`, `chat` routers
- Modify `requirements.txt` — +`requests`

**Frontend (`ui-student-py`)**
- Modify `src/pages/Login.js` — 3-role picker buttons
- Create `src/admin/AdminAnalytics.js` + `src/admin/analytics/*` — copied from `py-student-ui-asu`
- Modify `src/App.js` / `src/components/Navbar.js` — already wired for analytics/chat; verify

**DB (both `samsdb` + `MyStudentDb_v2`)** — DDL in Phase 0.

---

## Phase 0 — Database schema (SSMS, run against BOTH databases)

> No code tests here; verification is querying the table/columns back. Run each block in SSMS against `samsdb` AND `MyStudentDb_v2`.

### Task 0.1: Create `dbo.AdminAuditLog`

**Files:** SSMS only.

- [ ] **Step 1: Inspect existing `admin_audit_log`**

Run in SSMS (both DBs):
```sql
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'admin_audit_log';
SELECT COUNT(*) FROM dbo.admin_audit_log;
```
If columns already match the model below and you want the data, rename instead:
`EXEC sp_rename 'dbo.admin_audit_log', 'AdminAuditLog';` and SKIP step 2.

- [ ] **Step 2: Create the table (if recreating)**

```sql
CREATE TABLE dbo.AdminAuditLog (
    id          INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    admin_user  NVARCHAR(100)  NOT NULL,
    action_type NVARCHAR(50)   NOT NULL,
    [timestamp] DATETIME2      NOT NULL CONSTRAINT DF_AdminAuditLog_timestamp  DEFAULT SYSUTCDATETIME(),
    [status]    NVARCHAR(20)   NOT NULL,
    summary     NVARCHAR(500)  NULL,
    details     NVARCHAR(MAX)  NULL,
    created_at  DATETIME2      NOT NULL CONSTRAINT DF_AdminAuditLog_created_at DEFAULT SYSUTCDATETIME()
);
CREATE INDEX IX_AdminAuditLog_admin_user  ON dbo.AdminAuditLog (admin_user);
CREATE INDEX IX_AdminAuditLog_action_type ON dbo.AdminAuditLog (action_type);
CREATE INDEX IX_AdminAuditLog_timestamp   ON dbo.AdminAuditLog ([timestamp]);
```
Then drop the stub if empty: `DROP TABLE dbo.admin_audit_log;`

- [ ] **Step 3: Verify**

```sql
SELECT TOP 1 * FROM dbo.AdminAuditLog;  -- returns empty set, no error
```
Expected: query succeeds, 0 rows.

### Task 0.2: `user_access` RBAC flag columns

- [ ] **Step 1: Add columns (both DBs)**

```sql
ALTER TABLE dbo.user_access ADD analytics BIT NOT NULL CONSTRAINT DF_user_access_analytics DEFAULT 0;
ALTER TABLE dbo.user_access ADD chat      BIT NOT NULL CONSTRAINT DF_user_access_chat      DEFAULT 0;
```

- [ ] **Step 2: Verify**
```sql
SELECT analytics, chat FROM dbo.user_access;  -- columns exist
```

### Task 0.3: ClassSchedule term tables — analytics columns

- [ ] **Step 1: Add columns to each term table (both DBs)**

```sql
ALTER TABLE dbo.ClassSchedule2254 ADD ClassType NVARCHAR(5) NULL, ClassStatus NVARCHAR(5) NULL, AssocClassNum INT NULL;
ALTER TABLE dbo.ClassSchedule2261 ADD ClassType NVARCHAR(5) NULL, ClassStatus NVARCHAR(5) NULL, AssocClassNum INT NULL;
ALTER TABLE dbo.ClassSchedule2264 ADD ClassType NVARCHAR(5) NULL, ClassStatus NVARCHAR(5) NULL, AssocClassNum INT NULL;
```
(Skip any term table that does not exist in a given DB; note which exist.)

- [ ] **Step 2: Seed enrollment-section flags so analytics returns data**

Analytics `_enroll_sections` filters `ClassType='E' AND ClassStatus='A'`. Existing rows are NULL → would return nothing. Backfill demo rows:
```sql
UPDATE dbo.ClassSchedule2254 SET ClassType='E', ClassStatus='A' WHERE ClassType IS NULL;
UPDATE dbo.ClassSchedule2261 SET ClassType='E', ClassStatus='A' WHERE ClassType IS NULL;
UPDATE dbo.ClassSchedule2264 SET ClassType='E', ClassStatus='A' WHERE ClassType IS NULL;
```

- [ ] **Step 3: Verify**
```sql
SELECT COUNT(*) FROM dbo.ClassSchedule2254 WHERE ClassType='E' AND ClassStatus='A';  -- > 0
```

### Task 0.4: Assignment + Student parity columns

- [ ] **Step 1: Add columns (both DBs)**

```sql
ALTER TABLE dbo.StudentData ADD
    Prog_Reason_Descr NVARCHAR(100) NULL,
    Residency NVARCHAR(10) NULL,
    Residency_Status NVARCHAR(10) NULL,
    Market NVARCHAR(50) NULL;

ALTER TABLE dbo.StudentClassAssignments ADD
    Prog_Reason_Descr NVARCHAR(100) NULL,
    Residency NVARCHAR(10) NULL,
    Residency_Status NVARCHAR(10) NULL,
    Market NVARCHAR(50) NULL,
    Offer_Signed_Workday BIT NULL;
```
(If `Status` is absent on `StudentClassAssignments`, also: `ALTER TABLE dbo.StudentClassAssignments ADD [Status] NVARCHAR(MAX) NULL;`)

- [ ] **Step 2: Verify**
```sql
SELECT TOP 1 Prog_Reason_Descr, Residency, Residency_Status, Market FROM dbo.StudentData;
SELECT TOP 1 Offer_Signed_Workday FROM dbo.StudentClassAssignments;
```

- [ ] **Step 3: Commit (no code; note schema applied)**
```bash
git commit --allow-empty -m "chore(db): schema applied — AdminAuditLog, RBAC flags, analytics + parity cols (both DBs)"
```

---

## Phase 1 — Shared backend foundation (models, RBAC, deps)

> These unblock analytics + chat. After each model change, `Base.metadata.create_all` is a no-op against existing tables (columns already added in Phase 0). Verify by importing the app.

### Task 1.1: `require_perm` factory + analytics/chat flags in `dependencies.py`

**Files:**
- Modify: `dependencies.py`

**Interfaces:**
- Produces: `require_perm(flag: str) -> Callable` dependency factory (used by `routes/analytics.py`, `routes/chat.py`). Passes if `role=="admin"` or `is_admin` or `perms[flag]` truthy; else 403.

- [ ] **Step 1: Add the two flags to the flags dict**

In `dependencies.py`, in `current_user`, after the `"faculty_grader_uploads": bool(row.faculty_grader_uploads),` line, add:
```python
            "analytics": bool(row.analytics),
            "chat": bool(row.chat),
```

- [ ] **Step 2: Append the `require_perm` factory**

At end of `dependencies.py`:
```python
def require_perm(flag: str):
    """Dependency factory: allow admins or users whose perms[flag] is truthy; else 403."""
    def _dep(user: dict = Depends(current_user)) -> dict:
        perms = user.get("perms") or {}
        if user.get("role") == "admin" or user.get("is_admin") or perms.get(flag):
            return user
        raise HTTPException(status_code=403, detail="forbidden")
    return _dep
```
(Confirm `Depends` and `HTTPException` are imported at top — they are.)

- [ ] **Step 3: Verify import**

Run: `python -c "from dependencies import require_perm, current_user; print('ok')"`
Expected: `ok` (no import error). If `row.analytics`/`row.chat` raise at runtime later, the model column (Task 1.4) is missing — do Task 1.4 first if so.

- [ ] **Step 4: Commit**
```bash
git add dependencies.py && git commit -m "feat(auth): require_perm factory + analytics/chat flags"
```

### Task 1.2: `utils/rbac.py` ROLE_DEFAULTS

**Files:** Modify `utils/rbac.py`

- [ ] **Step 1: Add keys to each role**

In `ROLE_DEFAULTS`, add to EACH of the four dicts (`admin`, `program_chair`, `faculty_grader`, `default`):
- `admin`: `"analytics": True,` and `"chat": True,`
- `program_chair`, `faculty_grader`, `default`: `"analytics": False,` and `"chat": False,`

- [ ] **Step 2: Verify**

Run: `python -c "from utils.rbac import ROLE_DEFAULTS; assert ROLE_DEFAULTS['admin']['analytics'] and ROLE_DEFAULTS['admin']['chat']; assert not ROLE_DEFAULTS['faculty_grader']['analytics']; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**
```bash
git add utils/rbac.py && git commit -m "feat(rbac): analytics/chat role defaults"
```

### Task 1.3: `utils/users.py` flags

**Files:** Modify `utils/users.py`

- [ ] **Step 1: Add flags**

In `get_user_and_perms`, after `"faculty_grader_uploads": bool(row.faculty_grader_uploads),` add:
```python
            "analytics": bool(row.analytics),
            "chat": bool(row.chat),
```

- [ ] **Step 2: Commit**
```bash
git add utils/users.py && git commit -m "feat(rbac): analytics/chat flags in get_user_and_perms"
```

### Task 1.4: `user_access` model columns

**Files:** Modify `models/user_access.py`

- [ ] **Step 1: Add columns**

After the `faculty_grader_uploads = Column(...)` line:
```python
    analytics = Column(Boolean, default=False, nullable=False)
    chat = Column(Boolean, default=False, nullable=False)
```

- [ ] **Step 2: Verify**

Run: `python -c "from models.user_access import UserAccess; assert hasattr(UserAccess, 'analytics') and hasattr(UserAccess, 'chat'); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**
```bash
git add models/user_access.py && git commit -m "feat(model): user_access analytics/chat columns"
```

### Task 1.5: Define term models + analytics columns in `class_schedule.py`

**Files:** Modify `models/class_schedule.py`

**Interfaces:**
- Produces: `ClassSchedule2254`, `ClassSchedule2261`, `ClassSchedule2264` (all with identical column set incl. `ClassType`, `ClassStatus`, `AssocClassNum`); `ACTIVE_TERM` constant.

- [ ] **Step 1: Add the 3 analytics columns to `ClassSchedule2254`**

Inside the existing `ClassSchedule2254` class body add:
```python
    ClassType = Column(String(5), nullable=True)
    ClassStatus = Column(String(5), nullable=True)
    AssocClassNum = Column(Integer, nullable=True)
```
(Ensure `Integer` is imported from sqlalchemy.)

- [ ] **Step 2: Define 2261 and 2264 with the same columns**

Add two classes mirroring `ClassSchedule2254`'s columns exactly, changing only the class name + `__tablename__`:
```python
class ClassSchedule2261(Base):
    __tablename__ = "ClassSchedule2261"
    __table_args__ = {"schema": "dbo"}
    # ... identical column definitions to ClassSchedule2254, including ClassType/ClassStatus/AssocClassNum ...

class ClassSchedule2264(Base):
    __tablename__ = "ClassSchedule2264"
    __table_args__ = {"schema": "dbo"}
    # ... identical column definitions ...
```
Copy the full column list from `ClassSchedule2254` verbatim into each. (Reference for the column set: existing `ClassSchedule2254` body.)

- [ ] **Step 3: Add `ACTIVE_TERM` constant at module top**
```python
import os
ACTIVE_TERM = os.getenv("ACTIVE_TERM", "2264")
```

- [ ] **Step 4: Verify**

Run: `python -c "from models.class_schedule import ClassSchedule2254, ClassSchedule2261, ClassSchedule2264, ACTIVE_TERM; assert all(hasattr(m,'ClassType') for m in (ClassSchedule2254,ClassSchedule2261,ClassSchedule2264)); print(ACTIVE_TERM)"`
Expected: prints `2264` (or env value), no error.

- [ ] **Step 5: Commit**
```bash
git add models/class_schedule.py && git commit -m "feat(model): define 2261/2264 term tables + analytics cols + ACTIVE_TERM"
```

### Task 1.6: Assignment model columns

**Files:** Modify `models/assignment.py`

- [ ] **Step 1: Add columns**

In `StudentClassAssignment`, after the last existing column:
```python
    Prog_Reason_Descr = Column(String(100), nullable=True)
    Residency = Column(String(10), nullable=True)
    Residency_Status = Column(String(10), nullable=True)
    Market = Column(String(50), nullable=True)
    Offer_Signed_Workday = Column(Boolean, nullable=True)
```
(Ensure `Boolean` imported.)

- [ ] **Step 2: Verify + Commit**

Run: `python -c "from models.assignment import StudentClassAssignment as A; assert hasattr(A,'Offer_Signed_Workday') and hasattr(A,'Market'); print('ok')"`
```bash
git add models/assignment.py && git commit -m "feat(model): assignment parity cols + Offer_Signed_Workday"
```

### Task 1.7: Student model columns

**Files:** Modify `models/student.py`

- [ ] **Step 1: Add columns**

In `StudentLookup`, after the last existing column:
```python
    Prog_Reason_Descr = Column(String(100), nullable=True)
    Residency = Column(String(10), nullable=True)
    Residency_Status = Column(String(10), nullable=True)
    Market = Column(String(50), nullable=True)
```

- [ ] **Step 2: Verify + Commit**

Run: `python -c "from models.student import StudentLookup as S; assert hasattr(S,'Market'); print('ok')"`
```bash
git add models/student.py && git commit -m "feat(model): student parity cols"
```

### Task 1.8: Add `requests` dependency

**Files:** Modify `requirements.txt` (UTF-16 encoded — preserve encoding)

- [ ] **Step 1: Add `requests`**

Append a line `requests` to `requirements.txt`. (Use an editor that preserves UTF-16, or `pip install requests` then `pip freeze | grep -i requests` to get the pinned line.)

- [ ] **Step 2: Install + verify**

Run: `pip install requests && python -c "import requests; print(requests.__version__)"`
Expected: prints a version.

- [ ] **Step 3: Commit**
```bash
git add requirements.txt && git commit -m "chore(deps): add requests for chat gateway"
```

---

## Phase 2 — Analytics port

> Source: `StudentApi-asu/routes/analytics.py` (27 endpoints, prefix `/api/analytics`). Strategy A: map term→model; single-term queries pick the term table and drop the `Term` filter; the cross-term endpoints union the 3 tables in Python. Frontend already exists.

### Task 2.1: Port `analytics.py` — imports, helpers, single-term endpoints

**Files:**
- Create: `routes/analytics.py`
- Modify: `main.py`

**Interfaces:**
- Consumes: `require_perm` (Task 1.1), `ClassSchedule2254/2261/2264` + `ACTIVE_TERM` (Task 1.5), `StudentLookup`, `StudentClassAssignment`.
- Produces: `router` (APIRouter prefix `/api/analytics`).

- [ ] **Step 1: Copy source file as starting point**

Copy `StudentApi-asu/routes/analytics.py` → `StudentApi-py/routes/analytics.py` verbatim.

- [ ] **Step 2: Fix imports (top of file)**

Replace `from models.class_schedule import ClassSchedule, ACTIVE_TERM` with:
```python
from models.class_schedule import ClassSchedule2254, ClassSchedule2261, ClassSchedule2264, ACTIVE_TERM

TERM_MODELS = {"2254": ClassSchedule2254, "2261": ClassSchedule2261, "2264": ClassSchedule2264}
def _cls(term):
    return TERM_MODELS.get(str(term or ACTIVE_TERM), ClassSchedule2254)
```

- [ ] **Step 3: Make `_enroll_sections` take a model param**

Change `_enroll_sections()` to accept the term model and reference its columns:
```python
def _enroll_sections(M):
    return and_(M.ClassType == "E", M.ClassStatus == "A")
```
Update every call site to `_enroll_sections(M)` where `M = _cls(use_term)`.

- [ ] **Step 4: Rewrite single-term endpoints to use `_cls` and drop Term filter**

For each single-term endpoint (`/enrollment`, `/enrollment/by-subject`, `/enrollment/fill-rate-by-subject`, `/enrollment/top-instructors`, `/enrollment/mode-mix`, `/enrollment/kpis`, `/cross/grader-ratio-by-subject`, `/cross/cost-per-enrolled-by-subject`, `/enrollment/instructor-load`): set `M = _cls(term)` at the top, replace `ClassSchedule` with `M`, and DELETE any `.filter(ClassSchedule.Term == use_term)` clause (the table IS the term).

- [ ] **Step 5: Wire router into `main.py`**

In `main.py`, add `analytics` to the `from routes import ...` group and after `app.include_router(admin_users.router)` add:
```python
app.include_router(analytics.router)
```

- [ ] **Step 6: Verify app boots + a single-term endpoint works**

Run: `uvicorn main:app --port 8000` (separate shell), then:
```bash
curl -s "http://localhost:8000/api/analytics/enrollment/kpis?term=2254" -H "Cookie: auth=admin"
```
Expected: 200 JSON with kpi numbers (after a fake admin user exists — if 403/empty, seed admin in Task 5.1 first, or test with an existing admin asurite). App boots with no import error.

- [ ] **Step 7: Commit**
```bash
git add routes/analytics.py main.py && git commit -m "feat(analytics): port endpoints with term-table strategy (single-term)"
```

### Task 2.2: Rewrite cross-term analytics endpoints (Python-side union)

**Files:** Modify `routes/analytics.py`

- [ ] **Step 1: Union the dropdown/distinct endpoints**

For `/enrollment/subjects`, `/enrollment/instructors`, `/enrollment/catalogs`, `/enrollment/levels`: run the existing distinct query once per model in `TERM_MODELS.values()`, collect into a Python `set`, return sorted. Example for `/enrollment/subjects`:
```python
subjects = set()
for M in TERM_MODELS.values():
    for (s,) in db.query(M.Subject).filter(_enroll_sections(M)).distinct():
        if s: subjects.add(s)
return sorted(subjects)
```

- [ ] **Step 2: Union the cross-term metric endpoints**

For `/trend` (assignments-only — leave as-is, it doesn't touch ClassSchedule), `/enrollment/course-by-term`, `/enrollment/course-by-instructor`: loop over the 3 models, run the per-term aggregate, tag each result row with its term key, and merge lists in Python (no SQL `GROUP BY Term` across tables). Preserve the same response shape the frontend expects (term-keyed rows).

- [ ] **Step 3: Verify cross-term endpoint**

Run:
```bash
curl -s "http://localhost:8000/api/analytics/enrollment/subjects" -H "Cookie: auth=admin"
curl -s "http://localhost:8000/api/analytics/enrollment/course-by-term?metric=enrollment" -H "Cookie: auth=admin"
```
Expected: 200 JSON arrays; subjects list non-empty; course-by-term has rows tagged per term.

- [ ] **Step 4: Commit**
```bash
git add routes/analytics.py && git commit -m "feat(analytics): cross-term endpoints via Python-side union"
```

---

## Phase 3 — Chatbot port (read-only)

> Source: `StudentApi-asu/routes/chat.py` (prefix `/api/chat`, POST). Read-only: drop the `create_assignment` write tool and its TOOLS entry. Remap tables to term-suffixed names.

### Task 3.1: Add `VALID_POSITIONS` / `normalize_position` to `routes/assignment.py`

**Files:** Modify `routes/assignment.py`

**Interfaces:**
- Produces: `VALID_POSITIONS`, `normalize_position(p)` (imported by `routes/chat.py`).

- [ ] **Step 1: Copy the helpers from source**

Copy `VALID_POSITIONS` and `normalize_position` (asu `routes/assignment.py:25-56`) verbatim to the module top of py `routes/assignment.py`.

- [ ] **Step 2: Verify + Commit**

Run: `python -c "from routes.assignment import VALID_POSITIONS, normalize_position; print(normalize_position('grader'))"`
```bash
git add routes/assignment.py && git commit -m "feat(assignment): VALID_POSITIONS + normalize_position helpers"
```

### Task 3.2: `calculate_compensation` accepts `term` (no cap logic)

**Files:** Modify `utils/assignment_utils.py`, `routes/assignment.py`

- [ ] **Step 1: Add optional `term` param**

Change `def calculate_compensation(a):` → `def calculate_compensation(a, term=None):`. Do NOT add the summer-cap branch (decision: cols only). `term` is accepted but only used by the scrubbed cost-center routing if applicable; otherwise ignored.

- [ ] **Step 2: Pass `term=` at existing call sites**

In `routes/assignment.py`, update each `calculate_compensation({...})` call to pass `, term=class_obj.Term` (or the relevant term var) so the signature is exercised consistently.

- [ ] **Step 3: Verify + Commit**

Run: `python -c "from utils.assignment_utils import calculate_compensation; print(calculate_compensation({'Position':'Grader','WeeklyHours':10,'ClassSession':'C'}, term='2264'))"`
Expected: a number, no TypeError.
```bash
git add utils/assignment_utils.py routes/assignment.py && git commit -m "feat(comp): calculate_compensation accepts term (no cap)"
```

### Task 3.3: Port `chat.py` read-only with table remaps

**Files:**
- Create: `routes/chat.py`
- Modify: `main.py`

**Interfaces:**
- Consumes: `require_perm` (1.1), `normalize_position`/`VALID_POSITIONS` (3.1), `calculate_compensation(a, term=)` (3.2), term models (1.5), `StudentLookup`, `StudentClassAssignment`.

- [ ] **Step 1: Copy source file**

Copy `StudentApi-asu/routes/chat.py` → `StudentApi-py/routes/chat.py` verbatim.

- [ ] **Step 2: Remap imports + tables**

- Imports: replace `from models.class_schedule import ClassSchedule, ACTIVE_TERM` with the term models + `ACTIVE_TERM` (as Task 1.5). For class lookups, use `_cls(term)` resolver (copy the `TERM_MODELS`/`_cls` helper into chat.py too, or import from analytics).
- `StudentLookup` already maps to `StudentData` in py — no change (model class name is the same; tablename differs and is correct).
- `lookup_class` tool: query the term model directly, drop `Term == ACTIVE_TERM` filter.

- [ ] **Step 3: Drop the write tool (read-only)**

- Remove the `create_assignment` tool implementation function.
- Remove its entry from the `TOOLS` list (the `create_assignment` function schema).
- Remove any tool-dispatch branch that calls it.
- Keep the 4 read tools: `lookup_student`, `lookup_class`, `get_remaining_hours`, `get_class_assignments`.

- [ ] **Step 4: Drop reads of columns not present / not needed**

In the remaining read tools, remove reads of student columns that the leaner py models may not populate if they error; the parity columns (`Prog_Reason_Descr`,`Residency`,`Residency_Status`,`Market`) now EXIST on the models (Tasks 1.6/1.7) so they can stay. Verify no reference to `InstructorEmail` on assignment (py assignment lacks it) — remove if present.

- [ ] **Step 5: Keep gateway call + tool-result feedback verbatim**

Preserve the gateway quirk workaround (synthetic assistant+user messages for tool results) and `CREATEAI_*` env reading exactly.

- [ ] **Step 6: Wire router (ungated include; perm gate is in-route)**

In `main.py` add `chat` to imports and after analytics:
```python
app.include_router(chat.router)
```

- [ ] **Step 7: Verify**

Set `CREATEAI_API_KEY` in local `.env`. Run app, then:
```bash
curl -s -X POST "http://localhost:8000/api/chat" -H "Content-Type: application/json" -H "Cookie: auth=admin" -d '{"messages":[{"role":"user","content":"look up class 12345"}]}'
```
Expected: 200 with `{"reply": ...}`. If `CREATEAI_API_KEY` missing → 500 "Chat gateway is not configured" (expected without key). App boots; no import errors; no write tool in TOOLS.

- [ ] **Step 8: Commit**
```bash
git add routes/chat.py main.py && git commit -m "feat(chat): port read-only chatbot with term remaps"
```

---

## Phase 4 — Scrub real values

### Task 4.1: Scrub cost-centers + pay rates to fake

**Files:** Modify `utils/assignment_utils.py` (and any other file carrying the real codes — grep first)

**Fake replacement map (use consistently everywhere):**

| Real | Fake |
|---|---|
| `DR07557` | `DR00001` |
| `DR08243` | `DR00002` |
| `CC1139` | `CC9001` |
| `CC0136` | `CC9002` |
| `PG08491` | `PG90001` |
| `PG08524` | `PG90002` |
| every other real `PG#####` | `PG900NN` (sequential fakes) |
| pay rate `15.62` | `20.00` |
| pay rate `22.00` | `25.00` |

- [ ] **Step 1: Find all occurrences**

Run: `grep -rnE "DR07557|DR08243|CC1139|CC0136|PG0[0-9]{4}|15\.62|22\.00" utils/ routes/`
List every hit.

- [ ] **Step 2: Replace per the map**

Apply the fake map to every hit. Keep structure identical; only the literal values change. Bump `RULES_VERSION` to today's date string.

- [ ] **Step 3: Verify no real values remain**

Run: `grep -rnE "DR07557|DR08243|CC1139|CC0136|PG08491|PG08524|15\.62|22\.00" utils/ routes/`
Expected: NO matches.

- [ ] **Step 4: Sanity-run comp calc**

Run: `python -c "from utils.assignment_utils import calculate_compensation; print(calculate_compensation({'Position':'Grader','WeeklyHours':10,'ClassSession':'C'}, term='2264'))"`
Expected: a number (now using fake rate).

- [ ] **Step 5: Commit**
```bash
git add utils/assignment_utils.py routes/ && git commit -m "chore(scrub): replace real ASU cost-centers + pay rates with fakes"
```

---

## Phase 5 — Fake users + frontend

### Task 5.1: Seed 3 fake users

**Files:** SSMS (both DBs)

- [ ] **Step 1: Insert 3 role rows**

Pick fake asu_ids matching the Login buttons (Task 5.2 uses these). Set role flags via the role; explicit flags optional since `merged_perms` applies role defaults.
```sql
INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat,
    faculty_dashboard, applications, faculty_quickassign, faculty_grader_uploads)
VALUES ('demo_faculty', 'faculty_grader', 'Demo Faculty', 'faculty@example.edu', 1, 0, 0, 1, 1, 1, 1);

INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat,
    faculty_dashboard, applications, student_summary_page, bulk_upload_assignments,
    assignment_adder, program_chair_uploads)
VALUES ('demo_chair', 'program_chair', 'Demo Chair', 'chair@example.edu', 1, 0, 0, 1, 1, 1, 1, 1, 1);

INSERT INTO dbo.user_access (asu_id, role, name, email, login, analytics, chat, master_dashboard)
VALUES ('demo_admin', 'admin', 'Demo Admin', 'admin@example.edu', 1, 1, 1, 1);
```
(Admin gets all perms via `merged_perms` is_admin bypass anyway.)

- [ ] **Step 2: Verify**
```sql
SELECT asu_id, role, analytics, chat FROM dbo.user_access WHERE asu_id LIKE 'demo_%';
```
Expected: 3 rows.

### Task 5.2: Login.js 3-role picker

**Files:** Modify `ui-student-py/src/pages/Login.js`

- [ ] **Step 1: Replace manual input + tlorents link with 3 role buttons**

Replace the manual ASURITE `<input>` block and the "login as tlorents" quick link with three buttons calling the existing `impersonate(id)` handler with the seeded asu_ids: `demo_faculty`, `demo_chair`, `demo_admin`. Keep the `impersonate` function (it calls `/api/dev-impersonate?asurite=<id>`) unchanged. Label buttons "Login as Faculty", "Login as Program Chair", "Login as Admin".

- [ ] **Step 2: Verify in browser**

Run the frontend (`npm start` in `ui-student-py`), backend on :8000. Click each button → lands on `/` as that role; Navbar shows the role's items.
- Faculty: faculty dashboard items, no admin/master.
- Chair: chair uploads + applications, no master dashboard.
- Admin: everything incl. Analytics + Chat.

- [ ] **Step 3: Commit (in ui-student-py repo)**
```bash
git add src/pages/Login.js && git commit -m "feat(login): 3-role picker for portfolio RBAC demo"
```

### Task 5.3: Copy analytics dashboard components into ui-student-py

**Files:**
- Create: `ui-student-py/src/admin/AdminAnalytics.js`
- Create: `ui-student-py/src/admin/analytics/*` (ChartCard.js, HiringTab.js, EnrollmentTab.js, StudentPopulationTab.js, OtherTab.js, chartRenderers.js, useAnalytics.js)

- [ ] **Step 1: Copy from source frontend**

Copy `py-student-ui-asu/src/admin/AdminAnalytics.js` and the entire `py-student-ui-asu/src/admin/analytics/` directory into `ui-student-py/src/admin/`. (MUI X Charts already installed — no new deps.)

- [ ] **Step 2: Confirm App.js route + Navbar item resolve**

`ui-student-py/src/App.js` already has the `/analytics` route referencing `AdminAnalytics` and Navbar already has the analytics item (verified). Confirm the import path in App.js matches the copied file location; fix if needed.

- [ ] **Step 3: Verify in browser as admin**

Login as `demo_admin` → click Analytics → tabs render, charts pull from `/api/analytics/*`. Login as `demo_faculty` → no Analytics nav item.

- [ ] **Step 4: Commit (ui-student-py)**
```bash
git add src/admin && git commit -m "feat(analytics): dashboard components copied from source UI"
```

### Task 5.4: Verify chat widget end-to-end

**Files:** none (ChatWidget already exists in ui-student-py)

- [ ] **Step 1: Verify gating + round-trip**

With `CREATEAI_API_KEY` set on backend: login as `demo_admin` → chat widget responds. Login as `demo_faculty` (chat=0) → chat gated (403 / widget hidden per perm). Confirm read tools work (lookup a class/student); confirm NO create/write path exists.

- [ ] **Step 2: Final commit / PR**

Backend (`StudentApi-py`): push branch `feat/replica-sync-portfolio-rbac`, open PR.
Frontend (`ui-student-py`): commit + push its branch.

---

## Self-review notes

- **Spec coverage:** Auth (Task 5.1/5.2) ✔; AdminAuditLog (0.1) ✔; Analytics (Phase 2 + 5.3) ✔; RBAC flags (1.1–1.4) ✔; Schema/comp cols (0.3/0.4/1.5–1.7) ✔; Chatbot read-only (Phase 3 + 5.4) ✔; Scrub (Phase 4) ✔; Offer-letter excluded ✔.
- **Known divergences flagged in-task:** comp summer-cap NOT ported (cols only, per decision); chat write tool dropped (read-only, per decision).
- **Cross-DB:** every DDL block notes "both DBs". `ACTIVE_TERM` defaults to `2264` (source default) — overridable via env.
- **Dependency order:** Phase 0 (DB) → Phase 1 (models/RBAC) before Phase 2/3 (routes that import them). Task 1.4 (user_access cols) must precede any runtime hit of `current_user`.
