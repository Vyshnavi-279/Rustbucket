# Rustbucket
# Rustbucket — Backend Service

Rustbucket is an automated application security system designed to inspect GitHub repositories for security vulnerabilities, outdated software packages, and non-compliant open-source licenses. This directory contains the core backend API engine, background task processing pipeline, and database integration layer.

---

## 🛠️ Tech Stack & Dependencies

* **Framework:** FastAPI (Python 3.11 / 3.13)
* **Database & ORM:** PostgreSQL (Neon DB), SQLAlchemy, Alembic (Migrations)
* **Task Queue & Broker:** Celery, Redis
* **Integrations:** PyGithub REST API
* **Observability:** Prometheus FastAPI Instrumentator
* **Testing & Code Quality:** Pytest, HTTPX, Ruff

---

## 📁 Repository Structure

```text
backend/
├── alembic/              # Database migration scripts
├── app/
│   ├── config.py         # Environment settings & pydantic configuration
│   ├── crud.py           # Database CRUD helper functions
│   ├── db.py             # Database session and engine setup
│   ├── github_client.py  # PyGithub API adapter
│   ├── main.py           # FastAPI application & REST routes
│   ├── manifest_parser.py# Dependency file parser (package.json, requirements.txt)
│   ├── models.py         # SQLAlchemy database models
│   ├── scanner_adapter.py# Stub and real security scanner engine interface
│   ├── schemas.py        # Pydantic request/response models
│   └── worker.py         # Celery task definitions
├── tests/                # Automated pytest unit test suite
├── .dockerignore         # Docker ignore rules
├── .env.example          # Environment variable template
├── Dockerfile            # Container definition for backend service
├── requirements.txt      # Project Python dependencies
└── test_run.log          # Generated test execution logs
