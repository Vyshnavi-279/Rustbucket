# Contributing to Rustbucket

This is a 4-person team project with strict folder ownership so everyone can
build in parallel without blocking each other. Please read this before
opening a PR.

## Folder ownership

| Owner | Folders |
|---|---|
| Person 1 — Backend & Data | `backend/` |
| Person 2 — Scanning Engine | `scanner/` |
| Person 3 — Infra & CI/CD | `infra/`, `.github/`, root files (`docker-compose.yml`, `.env.example`, `README.md`, `.gitignore`, `LICENSE`) |
| Person 4 — Frontend & Observability | `frontend/`, `observability/` |

**Never edit a file in someone else's folder.** If you think a change is
needed there, open an issue or message the owner directly — don't just push
to it. This is what keeps merges conflict-free.

## Branching

Create one branch per task, named after the task:

```
p1/manifest-parser
p2/trivy-scan
p3/dockerfiles
p4/results-page
```

## Pull requests

1. Open a PR into `main` once your task passes its own self-test.
2. Because folders are never shared, your PR can be merged as soon as CI is
   green — no need to wait on the rest of the team.
3. Required checks (see `.github/workflows/ci.yml`): lint + test for
   whichever folder(s) your PR touches.
4. Fill out the PR template checklist: tests pass, the shared contract
   wasn't changed, and you self-tested the change.
5. Commit small and often, with messages like `scanner: add outdated check`.

## The shared contract

Section 2 of the team's work plan (data shapes, API routes, service names,
ports, and environment variables) is **final**. Don't renegotiate it while
building. If it's genuinely wrong, raise it with the whole team in writing
and fix the contract document first — code follows the contract, not the
other way around.

## Mocking dependencies

Every task should be finishable and testable by one person on one laptop.
If you'd otherwise be blocked waiting on someone else's part, build your own
stand-in for it (a stub scanner, a mock API server, a fake metrics
exporter, a placeholder container) rather than waiting.

## Integration

Integration is the only combined work, and it only starts once every
person's "Done checklist" is fully ticked. See Section 7 of the work plan
for the integration steps, bug-routing table, and demo script.
