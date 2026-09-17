# Automated Security Vulnerability Remediation Agent

Hackathon-ready reference implementation that turns normalized Prisma/Nexus-style findings into validated Maven remediation commits and optional GitHub pull requests.

Companion target repository: [vulnerable-java-platform](https://github.com/architbansal1310/vulnerable-java-platform)

The solution has two intentionally separated runtime components:

- A Java 21/Spring Boot REST decision service with DTO, Controller, Service, Repository, validation, structured errors, and a 20-record dataset.
- A dependency-free Python execution worker that performs Maven ownership analysis, branch creation, validation, commits, pushes, and pull requests.

## What the MVP demonstrates

- Ingests Critical and High findings from JSON reports.
- Maps Maven coordinates to the declaring child POM.
- Traces versionless dependencies to root `dependencyManagement` properties.
- Updates parent-managed and child-overridden versions.
- Refuses to mutate a dirty repository.
- Creates a dedicated `remediation/*` branch.
- Runs `mvn verify` before committing.
- Generates a consistent, review-oriented PR explanation without an LLM.
- Pushes and opens a GitHub PR only when explicitly requested.
- Never merges automatically.

The implementation uses Python's standard library, Git, Java 21, Spring Boot, and Maven. `vulnerable-java-platform` is the intentionally vulnerable target repository.

## Build and run the REST service

```powershell
./mvnw.cmd clean verify
./mvnw.cmd spring-boot:run
```

The API runs at `http://localhost:8081`. Verify it with:

```powershell
Invoke-RestMethod http://localhost:8081/actuator/health
```

Expected response:

```json
{"status":"UP"}
```

## REST API

### `POST /api/v1/remediations`

Validates and approves one remediation request. Approval is idempotent by finding and repository for the lifetime of the service process.

Example request:

```http
POST http://localhost:8081/api/v1/remediations
Content-Type: application/json

{
  "findingId": "CVE-2021-44228",
  "repository": "vulnerable-java-platform",
  "requestedFixedVersion": "2.17.1"
}
```

Approved response — HTTP `201 Created`:

```json
{
  "requestId": "generated-uuid",
  "status": "APPROVED",
  "findingId": "CVE-2021-44228",
  "repository": "vulnerable-java-platform",
  "dependency": "org.apache.logging.log4j:log4j-core",
  "severity": "CRITICAL",
  "currentVersion": "2.14.1",
  "fixedVersion": "2.17.1",
  "versionOwner": "parent",
  "message": "Eligible finding approved for branch creation, validation, and human-reviewed PR"
}
```

Error behavior:

| Condition | Status |
|---|---:|
| Invalid or missing fields | 400 |
| Unknown finding | 404 |
| Duplicate remediation | 409 |
| Ineligible severity, repository, or fixed version | 422 |

### `GET /api/v1/findings`

Returns all 20 mock scanner findings used by the demo.

### `GET /actuator/health`

Returns application readiness and liveness information.

Import [the Postman collection](postman/Security-Remediation-Agent.postman_collection.json) to execute six prepared requests with assertions.

## Quick start

From this directory, analyze the parent-managed example without changing files:

```powershell
./run.ps1 analyze `
  --report samples/nexus-parent-report.json `
  --repo ../vulnerable-java-platform
```

Run the dashboard:

```powershell
./start-dashboard.ps1
```

In the dashboard, use absolute paths for the target repository and either sample report. Click **Analyze** first. **Remediate** requires the target to be a clean Git repository and creates a real branch and commit.

CLI remediation:

```powershell
./run.ps1 remediate `
  --report samples/nexus-parent-report.json `
  --repo ../vulnerable-java-platform
```

## GitHub and live pull requests

The public repositories are already configured. Authenticate securely with Git Credential Manager when running from a new machine:

```powershell
git credential-manager github login
```

Run with `--open-pr`:

```powershell
./run.ps1 remediate `
  --report samples/nexus-parent-report.json `
  --repo ../vulnerable-java-platform `
  --open-pr
```

The agent reuses the credential stored by Git Credential Manager. `GITHUB_TOKEN` remains available for CI environments, but never commit or paste tokens into chat or source files.

## Report contract

```json
{
  "scanner": "NEXUS",
  "repository": "vulnerable-java-platform",
  "findings": [{
    "id": "CVE-2021-44228",
    "severity": "CRITICAL",
    "package": "org.apache.logging.log4j:log4j-core",
    "currentVersion": "2.14.1",
    "fixedVersion": "2.17.1",
    "module": "orders-api",
    "description": "Optional scanner description",
    "advisoryUrl": "https://example.invalid/advisory"
  }]
}
```

The MVP trusts the scanner-provided fixed version and supports direct Maven dependencies. Production extensions should independently verify advisory ranges, resolve transitive dependency trees, add policy controls, authenticate the API, persist runs, and sandbox builds.

## Tests

```powershell
./test-all.ps1
```

This runs five Python worker tests, 13 Java tests, the REST service's JaCoCo 70% coverage gate, both target Spring Boot modules, and both sample analyses without changing tracked files. The current measured Java line coverage is 93.4%; the HTML report is generated at `target/site/jacoco/index.html`.

## Deliverables

| Checklist item | Location |
|---|---|
| Filled problem template and idea | `Problem.md` |
| Build/run, API docs, examples | `README.md` |
| Before/after architecture | `ARCHITECTURE.md` |
| Significant prompt log | `PROMPTS.md` |
| Phased plan and done checks | `PLAN.md` |
| Layered Java source | `src/main/java` |
| Unit and controller tests | `src/test/java` |
| Postman collection | `postman/Security-Remediation-Agent.postman_collection.json` |
| 20-record dataset | `samples/mock-findings.json` |
| Execution worker | `remediator.py` and `server.py` |

Developer-only unit test command:

```powershell
python -m unittest discover -s tests -v
```

## Demo flow

1. Show `orders-api` without a dependency version and the root managed Log4j property at `2.14.1`.
2. Analyze `nexus-parent-report.json`; show that the agent selects the root POM.
3. Remediate; show the branch, Maven validation, and commit.
4. Push/open the human-reviewed PR after GitHub is configured.
5. Use a fresh checkout and repeat with `prisma-child-report.json` to show child override remediation.
6. Close with `renovate.json` as the production-scale dependency automation path.

> The sample target intentionally contains vulnerable versions. It is for local demonstration only and must not be deployed.
