# Student Hiring System API (Python FastAPI)

![Azure](https://img.shields.io/badge/hosted%20on-Azure_App_Service-blue)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688?logo=fastapi)
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)


## Live API (Swagger UI)

[https://studenthiringapp-d8cxb6h0e8eyevhf.westus-01.azurewebsites.net/docs](https://studenthiringapp-d8cxb6h0e8eyevhf.westus-01.azurewebsites.net/docs)

* Live Site (Frontend): [https://blue-moss-0cf2b2f10.1.azurestaticapps.net/](https://blue-moss-0cf2b2f10.1.azurestaticapps.net/)
* [Testing Data – Student Lookup Use Case](https://github.com/user-attachments/files/21176231/StudentData.pdf)


---

## About Me

I'm **Troy Lorents**, a full-stack engineer with 7+ years of experience designing and building secure, scalable applications.
This **Python FastAPI backend** powers the Student Hiring System and demonstrates my skills in API design, SQLAlchemy ORM, PostgreSQL/Azure SQL integration, and modern DevOps with Azure.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Getting Started](#getting-started)

   * [Clone Repository](#clone-repository)
   * [Configure Environment](#configure-environment)
   * [Run Locally](#run-locally)
5. [API Documentation](#api-documentation)
6. [Features & Endpoints](#features--endpoints)
7. [Deployment](#deployment)
8. [CI/CD](#cicd)
9. [Dev Highlights](#dev-highlights)
10. [License](#license)

---

## Overview

This project implements a **RESTful Web API** using **FastAPI** that powers the Student Hiring System. It exposes endpoints for:

* **Student Lookup**: search by ASUrite or 10-digit ID (`tlorents` or `123456789`)
* **Class Assignment**: assign students to classes with auto-calculated compensation and cost center
* **Bulk Upload**: ingest batches of hires with fewer required fields

  * includes **SQL Calibrate Preview** to enrich missing student/class details before commit
* **Student Summary**: view all assignments for a student and make edits
* **Dashboard**: provide hiring progress and administrative overview
* **Instructor Portal**: manage class assignments per instructor
* **Applications**: retrieve IA/Grader application submissions
* **Print Confirmation**: generate printable hiring statements

The API integrates with **Azure SQL/PostgreSQL** through SQLAlchemy and supports CORS for the React frontend.

---

## Tech Stack

* **Framework**: FastAPI (Python 3.11+)
* **ORM**: SQLAlchemy
* **Database**: Azure SQL / PostgreSQL
* **Documentation**: Swagger / ReDoc (auto-generated)
* **Hosting**: Azure App Service
* **CI/CD**: GitHub Actions
* **Tools**: Uvicorn, Alembic (migrations), Pydantic v2

---

## Prerequisites

* [Python 3.11+](https://www.python.org/downloads/)
* [Poetry](https://python-poetry.org/) or `pip` for dependency management
* [Azure CLI](https://learn.microsoft.com/cli/azure/) (for deployment)
* [Docker](https://www.docker.com/) (optional, for containerized dev)

---

## Getting Started

### Clone Repository

```bash
git clone https://github.com/tlorents-ASU/StudentApi.git
cd StudentApi
```

### Configure Environment

1. Copy `.env.example` → `.env`
2. Update environment variables:

```env
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:5432/<dbname>
ENV=development
```

3. (Optional) set additional keys:

   * `ALLOWED_ORIGINS`
   * `SECRET_KEY`

### Install & Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

Browse to:
👉 [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger)
👉 [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)

---

## API Documentation

Interactive OpenAPI docs available at:

```
https://studenthiringapp-d8cxb6h0e8eyevhf.westus-01.azurewebsites.net/docs
```

---

## Features & Endpoints

| Method | Endpoint                                                       | Description                                 |
| ------ | -------------------------------------------------------------- | ------------------------------------------- |
| GET    | `/api/StudentLookup/{id}`                                      | Get student by ID or ASUrite                |
| GET    | `/api/StudentClassAssignment`                                  | Get all assignments                         |
| GET    | `/api/StudentClassAssignment/{id}`                             | Get specific assignment                     |
| GET    | `/api/StudentClassAssignment/totalhours/{id}`                  | Get total hours assigned to student         |
| GET    | `/api/StudentClassAssignment/student-summary/{id}`             | Get summary + session totals for student    |
| POST   | `/api/StudentClassAssignment`                                  | Create assignment                           |
| PUT    | `/api/StudentClassAssignment/{id}`                             | Update assignment fields                    |
| POST   | `/api/StudentClassAssignment/bulk-edit`                        | Bulk edit multiple assignments              |
| POST   | `/api/StudentClassAssignment/upload`                           | Upload batch assignments from CSV/XLSX      |
| POST   | `/api/StudentClassAssignment/calibrate-preview`                | Preview/validate batch upload before commit |
| GET    | `/api/StudentClassAssignment/template`                         | Download CSV upload template                |
| GET    | `/api/class/subjects?term=2254`                                | Get available class subjects                |
| GET    | `/api/class/catalog?term=2254&subject=CSE`                     | Get catalog numbers for subject             |
| GET    | `/api/class/classnumbers?term=2254&subject=CSE&catalogNum=100` | Get class numbers                           |
| GET    | `/api/class/details/{classNum}?term=2254`                      | Get full class details                      |
| GET    | `/api/MastersIAGraderApplication`                              | Retrieve application submissions            |
| GET    | `/api/manage-assignments/by-instructor/{id}`                   | Get assignments by instructor               |
| PUT    | `/api/manage-assignments/{id}`                                 | Update assignment (instructor view)         |
| GET    | `/healthz`                                                     | Health check endpoint                       |

---

## Deployment

This API is deployed to **Azure App Service** with continuous delivery via GitHub Actions.

Workflow:

1. On push to `main`, GitHub Actions builds + runs tests
2. App is packaged with `uvicorn`/FastAPI
3. Deployment to Azure App Service

See [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

---

## CI/CD

* **Build**: Python install + linting/tests on each PR
* **Test**: Unit and integration tests (Pytest)
* **Deploy**: Azure App Service with zero-downtime swap

---

## Dev Highlights

* **Dynamic Compensation Logic**: calculates pay period & cost center automatically
* **Bulk Upload Preview**: validates student & class info before commit
* **CORS**: enabled for React frontend
* **Swagger / OpenAPI**: rich interactive docs
* **Error Handling**: Pydantic validation + structured HTTPException responses
* **DB Models**: SQLAlchemy ORM with migrations

---

### Created by Troy Lorents | @TroyJLorents-GH

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.


---

Do you also want me to create a **badges section** (e.g. GitHub Actions CI badge, Python version badge, FastAPI docs badge) like we see in open source repos, so it looks more professional on GitHub?
