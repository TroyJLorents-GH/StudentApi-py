# Design — Portfolio Replica Sync + Fake-User RBAC

**Date:** 2026-06-23
**Repos in play:**
- Backend (this) — `StudentApi-py` → portfolio replica
- Frontend (replica) — `ui-student-py`
- Source of truth — `StudentApi-asu` + `py-student-ui-asu` (work, daily, real data, CAS SSO)

## Goal

Make the replica pair (`ui-student-py` + `StudentApi-py`) behave like the source pair
(`py-student-ui-asu` + `StudentApi-asu`), with two intentional differences:

1. **No CAS SSO.** Source uses ASU CAS (`auth_cas.py`). Replica uses 3 fake users + a
   role-picker so portfolio viewers can experience RBAC from each role's view.
2. **No real data.** Cost-center numbers changed/faked; no real student PII.

Plus: bring the replica up to date with new features merged into the source.

## Current state (verified)

- Both backends share an identical RBAC engine (`utils/rbac.py` `merged_perms` + `ROLE_DEFAULTS`).
- Replica backend already exposes the dev-impersonate machinery at `/api/*`
  (`/api/user`, `/api/dev-impersonate?asurite=X`, `/api/dev-logout`). Cookie `auth`=asurite.
- Replica frontend `ui-student-py` is already a copy of the source frontend:
  `AuthContext.js` (CAS / dev / mock branches), `Login.js` (calls dev-impersonate),
  `RouteGuard.js`, perm-gated `Navbar.js`. Currently runs in **dev mode** (`USE_CAS=false`).
- Replica is **behind** the source by several feature merges (analytics, chatbot, offer-letter,
  schema/comp changes).

### DB connection reality

- `StudentApi-py/.env` `DATABASE_URL` points to **local** SQL Express
  (`Troyjl\SQLEXPRESS` / `samsdb`, Windows trusted auth) — NOT Azure.
- Deployed Azure App Service overrides `DATABASE_URL` via **App Service → Configuration**
  (Azure SQL login + password, DB `MyStudentDb_v2`).
- Schema changes below must be applied to **both** local `samsdb` and Azure `MyStudentDb_v2`.

## Scope — decisions locked

### 1. Auth — Option A (fake users + role-picker)

- No CAS. Keep `USE_CAS=false`. No CAS code runs.
- Seed 3 rows in `dbo.user_access` (fake asu_ids), roles:
  `faculty_grader`, `program_chair`, `admin`.
- Replace `Login.js` manual ASURITE box + "login as tlorents" with **3 role buttons**;
  each calls `/api/dev-impersonate?asurite=<that user>` then refreshes auth context.
- Backend RBAC (`user_access` row → `merged_perms`) drives which views/nav each role sees.
  This deliberately exercises the real RBAC engine — the portfolio showpiece.

### 2. DB table — add `dbo.AdminAuditLog`

Model `models/admin_audit_log.py` maps to `AdminAuditLog`; Azure DB only has
`admin_audit_log` (name mismatch → ORM "table not found"). PhD table NOT needed.

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

Decide rename vs recreate after inspecting existing `admin_audit_log` columns. Note:
`ClassSchedule2261`/`2264` are different term codes (new way stacks terms) — leave as-is.

### 3. Feature sync from source (`StudentApi-asu`)

Selected: **Analytics (1)**, **RBAC flags (3)**, **Schema/comp parity (5)**, **Chatbot (2)**.
Excluded: **Offer-letter (4)** — uses `pywin32` Word COM, Windows-only, breaks on Azure Linux.

| # | Feature | Backend | DB columns | Frontend |
|---|---|---|---|---|
| 1 | Analytics | port `routes/analytics.py` (+ lookup endpoints) | ClassSchedule +`ClassType`,`ClassStatus`,`AssocClassNum` (map only; cols exist in source DB) | analytics dashboard page + nav (gated by `analytics`) |
| 3 | RBAC flags | `rbac.py` ROLE_DEFAULTS +`analytics`,`chat`; flag list in `dependencies.py`/`utils/users.py`; `models/user_access.py` +cols | `user_access` +`analytics`,`chat` (+ any others in source diff) | nav/route gates on `analytics`,`chat` |
| 5 | Schema/comp | assignment/student/manage route + calc changes (summer 40hr, costCenter DR# kept faked) | `Prog_Reason_Descr`,`Residency`,`Residency_Status`,`Market` on assignment/student; `status` on StudentClassAssignments | columns surface where shown |
| 2 | Chatbot | port `routes/chat.py` + gateway utils | (covered by `chat` flag in #3) | chat UI, gated by `chat` perm |

#### Chatbot LLM backend

Uses ASU CreateAI gateway (`CREATEAI_BASE_URL=https://api-main.aiml.asu.edu`,
`CREATEAI_API_KEY`, model `aws/claude4_8_opus`), OpenAI-style `/v1/chat/completions` + tools.
User confirmed the ASU gateway key works for them.

- Store `CREATEAI_API_KEY` in **Azure App Service → Configuration** only — never commit.
- Verify gateway reachable from Azure outbound IP. If it 403s from Azure egress, fall back to
  a public OpenAI-compatible provider (one base_url + key swap).

## Sequencing

1. **DB schema** — add `AdminAuditLog`; add new columns to local `samsdb` + Azure `MyStudentDb_v2`.
2. **Backend model updates** — map new columns (ClassSchedule, assignment, student, user_access).
3. **Backend ports** — `analytics.py`, `chat.py` + gateway utils, schema/comp route+calc changes;
   wire routers in `main.py`.
4. **RBAC flags** — `rbac.py`, `dependencies.py`, `utils/users.py`.
5. **Frontend wiring** — analytics dashboard, chat UI, nav/route gates for new perms.
6. **Fake users + role-picker** — seed 3 `user_access` rows; rebuild `Login.js` as 3-role picker.
   Done last so it ties the RBAC views together for the demo.

## Out of scope / guardrails

- No CAS, no offer-letter feature.
- No real student data; cost-center numbers stay faked.
- Source repo (`StudentApi-asu` / `py-student-ui-asu`) is read-only reference — do not modify.
- Secrets (`CREATEAI_API_KEY`, DB password) live in Azure config, not in git.
