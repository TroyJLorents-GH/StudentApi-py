---
project: projects/StudentApi-py
type: services
---

# Hosted Services — StudentApi-py (SAMS API)

External, hosted services this backend depends on at build, deploy, or runtime.

---

## Microsoft Azure — App Service

* **Role:** Production hosting for the FastAPI backend (Linux, Python app, Gunicorn +
  Uvicorn workers).
* **Live URL:** `https://studenthiringapp-d8cxb6h0e8eyevhf.westus-01.azurewebsites.net`
  (Swagger UI at `/docs`).
* **Deploy slot:** `Production`, deployed via `azure/webapps-deploy@v3`.
* **Build:** Azure **Oryx** performs the dependency install/build on the platform after
  the GitHub Actions artifact upload.
* **Configuration:** Runtime secrets (`DATABASE_URL`, `ACTIVE_TERM`, `SESSION_SECRET`,
  and the CreateAI gateway token/URL/model) are set in **App Service → Configuration**,
  overriding any committed values.

## Microsoft Azure — SQL Database (Azure SQL)

* **Role:** Primary relational datastore (SQL Server / `dbo` schema), accessed through
  SQLAlchemy + pyodbc.
* **Connection:** Supplied via the `DATABASE_URL` environment variable (full SQLAlchemy
  URL or a raw ODBC string). Local development can substitute SQL Server Express with a
  trusted-auth ODBC connection.

## Microsoft Azure — Static Web Apps (related, separate repo)

* **Role:** Hosts the React frontend (`ui-student-py`), which calls this API.
* **Live URL:** `https://blue-moss-0cf2b2f10.1.azurestaticapps.net`
* **Integration here:** Its origin is allow-listed in the CORS configuration in `main.py`;
  not deployed by this repository.

## Managed AI Gateway (LLM provider)

* **Role:** LLM backend for the **IRA** support chatbot (`routes/chat.py`).
* **Endpoint:** OpenAI-compatible `/v1/chat/completions`; base URL configured via
  `CREATEAI_BASE_URL`.
* **Model:** **Claude Opus 4.8** via `aws/claude4_8_opus` (`CREATEAI_MODEL`).
* **Auth:** Single Bearer token, `CREATEAI_API_KEY`. Chat
  returns HTTP 500 if the token is unset.
* **Note:** A managed AI gateway fronting an AWS-hosted Anthropic Claude model;
  the app does not call the Anthropic API directly.

## GitHub Actions (CI/CD)

* **Role:** Build and deploy pipeline (`.github/workflows/`). Builds on Python 3.13,
  installs dependencies, uploads the artifact, and deploys to Azure App Service.
* **Auth:** Azure OIDC federated credentials (no stored publish profile / long-lived secret).

---

> The production system additionally integrates **CAS single sign-on**, but CAS is
> intentionally **disabled in this portfolio replica** (replaced by cookie-based dev
> impersonation), so it is not an active runtime dependency of this repository.
