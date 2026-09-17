# Architecture and Production Evolution

## MVP boundary

The hackathon implementation deliberately supports one reliable golden path: normalized Critical/High findings for directly declared Maven dependencies. It proves ingestion, prioritization, version ownership, safe modification, validation, Git branching, and human-reviewed pull-request preparation.

```text
Mock Prisma/Nexus JSON
          |
          v
 Report validation + severity policy
          |
          v
 Maven ownership analyzer
   | parent property | child version |
          |
          v
 Dedicated remediation branch
          |
          v
 Maven verify -> commit -> optional push/PR
```

## Components

- `remediator.py`: report model, severity policy, Maven analyzer/editor, validation, Git operations, PR evidence, and GitHub REST integration.
- `server.py`: local HTTP API for analyze/remediate operations.
- `static/index.html`: zero-build dashboard for a reliable demo.
- `samples/`: scanner-shaped normalized reports backed by real public advisories.
- `tests/`: parent ownership, child ownership, severity filtering, and stale-report safety tests.
- `vulnerable-java-platform`: separate target repository with root dependency management and two Spring Boot modules.

## Safety decisions

- Reject unsupported or malformed report data.
- Process only Critical and High severities.
- Reject stale findings when the reported version differs from the current POM.
- Require a clean Git worktree.
- Check Maven availability before branching.
- Replace exactly one expected XML value; ambiguous edits fail closed.
- Validate the full Maven reactor before committing.
- Require explicit flags for push and PR creation.
- Never merge automatically.
- Read the GitHub token only from the process environment.

## Production architecture

At enterprise scale, split the MVP into independently scalable services:

1. Scanner adapters consume Prisma, Nexus, GitHub, and other findings into a versioned event schema.
2. An inventory service maps packages, manifests, repositories, owners, and internal BOMs.
3. A policy engine handles severity, exploitability, reachability, exceptions, maintenance windows, and change budgets.
4. Renovate performs ecosystem-aware dependency discovery and standard update PR generation.
5. A remediation orchestrator handles shared BOM releases and downstream repository fan-out.
6. Ephemeral isolated workers build untrusted branches with restricted network and credentials.
7. An evidence store records input findings, decisions, diffs, test results, approvals, and audit history.
8. A dashboard reports backlog, mean time to remediate, success rate, and required human actions.

AI should remain advisory: summarize release notes, explain compatibility risk, select relevant tests, and diagnose failures. Version-range enforcement, edits, permissions, and merge gates should stay deterministic.

## Where Renovate fits

Renovate should become the production dependency-update engine for supported package managers. The surrounding platform adds scanner normalization, organization policy, shared-parent coordination, validation evidence, audit state, and exception workflows. The target repository includes `renovate.json` with vulnerability PRs enabled and automatic merge disabled.

## Known MVP limitations

- Direct Maven dependencies only; no transitive dependency-tree remediation.
- Scanner-provided fixed versions are trusted after stale-version validation.
- XML editing supports ordinary dependency and property declarations, not every Maven profile or inherited-property arrangement.
- Local dashboard has no authentication and must remain bound to loopback.
- No database, queue, retry scheduler, or multi-repository transaction coordinator.
- GitHub REST is implemented, but a real push/PR requires a user-created repository and fine-grained token.
