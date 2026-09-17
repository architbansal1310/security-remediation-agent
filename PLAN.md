# Phased Build Plan

## Phase 1 — Submission contract and repository skeleton

- Milestone: translate the hackathon checklist into project-specific deliverables.
- Done means: `Problem.md`, `README.md`, `ARCHITECTURE.md`, `PROMPTS.md`, and `PLAN.md` exist and contain no template placeholders except the intentionally blank `case_study` field.

## Phase 2 — REST decision service

- Milestone: implement Java 21/Spring Boot DTO, Controller, Service, Repository, and error-handling layers.
- Done means: the service starts on port 8081; `GET /actuator/health` returns `UP`; eligible remediation returns HTTP 201; duplicates return 409; ineligible findings return 422; unknown findings return 404; malformed input returns 400.

## Phase 3 — Remediation execution worker

- Milestone: normalize reports, locate Maven version ownership, update one expected value, validate, commit, push, and open a human-reviewed PR.
- Done means: parent- and child-owned samples both produce a dedicated branch and pass the complete target Maven reactor before commit.

## Phase 4 — Test evidence and datasets

- Milestone: cover approval, duplicates, eligibility failure, repository mismatch, version mismatch, unknown findings, malformed input, and dataset loading.
- Done means: `mvn verify` passes the JaCoCo 70% line-coverage gate; Python tests pass; the dataset contains exactly 20 records; the Postman collection contains at least three executable cases.

## Phase 5 — Demo and GitHub delivery

- Milestone: provide one-command verification, visual analysis dashboard, a three-minute script, and public repositories.
- Done means: `test-all.ps1` finishes with “All tests and analyses passed”; the dashboard loads locally; both repositories use `main`; README files cross-link; no credentials or generated build output are committed.

## Production follow-on

- Add authenticated scanner webhooks and durable queueing.
- Resolve transitive dependencies and multi-repository BOM releases.
- Run builds in isolated ephemeral workers with restricted credentials/network.
- Persist decision, test, approval, and exception evidence.
- Integrate Renovate as the multi-ecosystem update engine.
- Add SSO/RBAC, rate limits, retries, observability, and policy administration.
