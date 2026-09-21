# Rustbucket

**Open Source Dependency Health Platform**
*Don't let your dependencies rust away.*

[![CI](https://github.com/Vyshnavi-279/rustbucket/actions/workflows/ci.yml/badge.svg)](https://github.com/Vyshnavi-279/rustbucket/actions/workflows/ci.yml)
[![Build & Push Images](https://github.com/Vyshnavi-279/rustbucket/actions/workflows/images.yml/badge.svg)](https://github.com/Vyshnavi-279/rustbucket/actions/workflows/images.yml)



## Overview

Rustbucket scans any public GitHub repository's dependency manifest
(`package.json` or `requirements.txt`) and reports back:

- **Known vulnerabilities (CVEs)** via Trivy, with an OSV.dev fallback
- **Outdated dependencies** compared against the latest registry versions
- **License conflicts** between your project's license and its dependencies
- A single **health score (0–100)** summarizing all of the above

Submit a repo URL, watch a background scan run, and get a dashboard with a
score gauge, vulnerability/outdated/license tables, and a historical trend
per repository.

## Features

- 🔍 Async scanning — submit a URL, get a `scan_id` instantly, poll for results
- 🛡️ CVE detection via Trivy (with OSV.dev as a fallback scanner)
- 📦 Outdated-dependency detection (major / minor / patch)
- ⚖️ License conflict detection (permissive vs. copyleft vs. network-copyleft)
- 📊 Health score with a documented, reproducible formula
- 📈 Historical score tracking per repository
- 📡 Full observability: Prometheus metrics + a live Grafana dashboard
- 🚀 One-command local stack (Docker Compose) and a Kubernetes deployment (Minikube)

## Architecture

```mermaid
flowchart LR
    Browser["Browser"] --> Nginx["nginx + React (frontend)"]
    Nginx -->|"/api/*"| Backend["FastAPI backend"]
    Backend --> Neon[("Neon Postgres")]
    Backend --> Redis[("Redis")]
    Redis --> Worker["Celery worker"]
    Worker --> Scanner["Scanner (run_scan)"]
    Scanner --> Trivy["Trivy"]
    Scanner -.-> OSV["OSV.dev (fallback)"]
    Worker --> GitHub["GitHub API"]
    Backend -->|"/metrics"| Prometheus["Prometheus"]
    Worker -->|"/metrics"| Prometheus
    Prometheus --> Grafana["Grafana"]
    GHA["GitHub Actions"] -->|"build, scan, push"| GHCR[("GHCR")]
    GHCR --> K8s["Kubernetes (Minikube)"]
    K8s --> Backend
    K8s --> Worker
    K8s --> Nginx
```

A static export of this diagram is also kept at `docs/architecture.png`.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), Tailwind CSS, Recharts |
| Backend API | FastAPI, Pydantic, Uvicorn |
| Database | Neon (managed Postgres), SQLAlchemy, Alembic |
| Background jobs | Celery + Redis |
| Scanning engine | Trivy, OSV.dev, `packaging` |
| Containers | Docker, Docker Compose |
| Orchestration | Kubernetes (Minikube for local/demo) |
| CI/CD | GitHub Actions, GHCR |
| Observability | Prometheus, Grafana |

## Repository layout

```
rustbucket/
├── backend/         Person 1 — FastAPI app, Celery worker, Alembic, tests
├── scanner/         Person 2 — CVE scan, outdated check, license rules, scoring
├── frontend/        Person 4 — React (Vite) dashboard
├── observability/   Person 4 — Prometheus, Grafana, dev fake exporter, k8s manifests
├── infra/           Person 3 — Dockerfiles, nginx, k8s manifests, scripts, placeholders
├── .github/         Person 3 — CI/CD workflows, CODEOWNERS, PR template
├── docker-compose.yml
├── .env.example
└── README.md
```

Full folder ownership and the fixed interfaces every part is built against
are documented in the team's internal work plan (shared contract).

## Quick start — Docker Compose

1. Copy the environment template and fill in real values:
   ```bash
   cp .env.example .env
   ```
2. Start the full stack:
   ```bash
   docker compose up --build
   ```
   To run it with placeholder services only (no real backend/scanner/frontend code needed yet):
   ```bash
   docker compose -f docker-compose.yml -f infra/docker-compose.placeholders.yml up --build
   ```
3. Open the app: **http://localhost:8080**
4. API docs (Swagger): **http://localhost:8000/docs**

To also bring up Prometheus + Grafana locally:

```bash
docker compose -f docker-compose.yml -f observability/docker-compose.observability.yml up --build
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## Deploying to Minikube

```bash
minikube start
infra/scripts/deploy-minikube.sh --local-images
```

This applies every manifest in `infra/k8s/`, waits for each Deployment to
roll out, and prints the frontend URL. To also deploy Prometheus/Grafana:

```bash
kubectl apply -f observability/k8s/
minikube service grafana -n rustbucket
```

Tear everything down:

```bash
infra/scripts/teardown.sh
```

Run a smoke test against any base URL (Compose or Minikube):

```bash
infra/scripts/smoke-test.sh http://localhost:8080
```

## Environment variables

| Variable | Used by | Meaning |
|---|---|---|
| `DATABASE_URL` | backend, worker | `postgresql+psycopg2://user:pass@host/db?sslmode=require` (Neon) |
| `REDIS_URL` | backend, worker | `redis://redis:6379/0` (local dev: `redis://localhost:6379/0`) |
| `GITHUB_TOKEN` | backend, worker | GitHub personal access token (read-only, public repos) |
| `SCANNER_MODE` | worker | `stub` (fake result, no scanner needed) or `real` (calls `scanner.run_scan`) |
| `CORS_ORIGINS` | backend | Comma-separated allowed origins, e.g. `http://localhost:5173` |

See `.env.example` for a fully annotated template.

## API summary

| Endpoint | Description |
|---|---|
| `POST /api/scans` | Queue a new scan for a `repo_url`. Returns `202` with `scan_id`. |
| `GET /api/scans/{scan_id}` | Poll scan status/result (`queued` → `running` → `done`/`failed`). |
| `GET /api/repos` | List every scanned repo with its latest score. |
| `GET /api/repos/{repo_id}/history` | Score history for one repo, oldest first. |
| `GET /health` | Liveness check. |
| `GET /metrics` | Prometheus metrics (backend on `:8000`, worker on `:8001`). |

Full request/response shapes are documented in Swagger at `/docs` once the
backend is running, and in the team's shared contract document.

## Running tests

| Folder | Command |
|---|---|
| `backend/` | `pytest backend -m "not network"` |
| `scanner/` | `pytest scanner -m "not network"` |
| `frontend/` | `npm test` (inside `frontend/`) |

Linting: `ruff check backend`, `ruff check scanner`, `npm run lint` (frontend).
Tests requiring real internet access or the Trivy binary are marked
`@pytest.mark.network` and are skipped in CI.

## CI/CD

- **`ci.yml`** — runs on every PR and push to `main`: lint + test for
  `backend/`, `scanner/`, and `frontend/` in parallel.
- **`images.yml`** — runs on push to `main`: builds the three Docker images,
  scans each with Trivy (blocking on `CRITICAL` findings), then pushes to
  GHCR tagged with the commit SHA and `latest`.

## Future work

See [Future Work](#future-work-details) below for ideas deliberately left
out of v1, including automated dependency-bump PRs, Slack/Discord
notifications, Kafka event streaming, GitOps with ArgoCD, Terraform-managed
cloud infra, static code-quality analysis, additional package ecosystems
(Maven, Go modules, Cargo, RubyGems), and scheduled re-scans.

<!-- screenshots -->

<!-- demo video -->

---

### Future work details

| Idea | What it would add |
|---|---|
| Automated pull requests | A bot that opens PRs bumping vulnerable dependencies to the fixed version |
| Slack / Discord notifications | Alerts when a scan completes or a score drops |
| Kafka event streaming | Decouple scan events from consumers (notifications, analytics) at scale |
| GitOps with ArgoCD | Deployments driven by Git commits instead of scripts |
| Terraform-provisioned cloud | Reproducible cloud infrastructure instead of Minikube |
| Code-quality analysis (OWASP, SonarQube) | Static analysis of the project's own source code, beyond dependencies |
| More ecosystems | Maven, Go modules, Cargo, RubyGems and lockfile-aware scanning |
| Scheduled re-scans | Nightly scans so history builds automatically |

## License

MIT — see [LICENSE](./LICENSE).
