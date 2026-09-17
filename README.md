# Automated Security Vulnerability Remediation Agent

Hackathon-ready reference implementation that turns normalized Prisma/Nexus-style findings into validated Maven remediation commits and optional GitHub pull requests.

Companion target repository: [vulnerable-java-platform](https://github.com/architbansal1310/vulnerable-java-platform)

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

The implementation uses only Python's standard library, Git, Java 21, and Maven. `vulnerable-java-platform` is the intentionally vulnerable target repository.

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

## GitHub setup

After creating your GitHub account:

1. Create two empty repositories named `security-remediation-agent` and `vulnerable-java-platform`.
2. Add each GitHub repository as the `origin` remote of the matching local repository and push `main`.
3. Create a fine-grained token limited to `vulnerable-java-platform` with **Contents: read/write** and **Pull requests: read/write**.
4. Set it only for the current terminal:

```powershell
$env:GITHUB_TOKEN = "your-token"
```

5. Run with `--open-pr`:

```powershell
./run.ps1 remediate `
  --report samples/nexus-parent-report.json `
  --repo ../vulnerable-java-platform `
  --open-pr
```

Do not commit tokens. The token is read only from `GITHUB_TOKEN`.

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
./run.ps1 --help
```

Developer test command (using an available Python executable):

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
