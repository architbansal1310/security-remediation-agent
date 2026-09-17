# Expected Deliverables Checklist

- [x] `Problem.md` — completed from the supplied template.
- [x] Hackathon theme and idea details — included in `Problem.md`.
- [x] `README.md` — problem overview, prerequisites, build/run steps, API contract, requests, responses, errors, testing, and demo flow.
- [x] `ARCHITECTURE.md` — one-page before/after legacy batch-to-REST diagrams plus component and production architecture.
- [x] `PROMPTS.md` — significant prompts, responses, decisions, and refinements; credentials excluded.
- [x] `PLAN.md` — phased milestones with explicit done-means checks.
- [x] Source code — Java DTO, Controller, Service, Repository, model, exception layers, plus Python execution worker.
- [x] Unit tests — approval, duplicate, eligibility, mismatch, unknown, validation, dataset, controller mapping, stale finding, parent/child ownership, and severity filtering.
- [x] 70%+ coverage — JaCoCo gate at 70%; current measured Java line coverage is 93.4%.
- [x] Postman collection — six requests with assertions in `postman/`.
- [x] Sample dataset — 20 mock records in `samples/mock-findings.json`.
- [x] Runnable application — Spring Boot executable JAR and Maven Wrapper; live HTTP checks verified.
- [x] Unified test command — `./test-all.ps1`.
- [x] CI — GitHub Actions runs Java coverage and self-contained Python worker tests.
- [x] Public source — GitHub `main` branch with no credentials or generated build output.
