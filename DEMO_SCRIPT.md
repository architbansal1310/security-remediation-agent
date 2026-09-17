# Three-Minute Demo Script

## 1. Set the problem — 20 seconds

“Security scanners find more dependency vulnerabilities than teams can manually remediate. Remedy converts a scanner finding into a tested, review-ready code change while keeping a human at the merge gate.”

## 2. Show the target — 30 seconds

Open the root `pom.xml` and show `log4j.version` at `2.14.1`. Open `orders-api/pom.xml` and show that `log4j-core` has no local version. Explain that the platform must trace ownership to the parent rather than making a bad child override.

## 3. Analyze — 35 seconds

Start the dashboard with `./start-dashboard.ps1`. Enter the absolute target-repository path and `samples/nexus-parent-report.json`. Click **Analyze**. Point out:

- Critical Log4Shell finding.
- Current and fixed versions.
- Parent ownership.
- Exact file selected for change.

## 4. Remediate — 60 seconds

Click **Remediate**. Explain the gates while Maven runs:

- Clean-repository enforcement.
- Dedicated branch.
- Exact version-only edit.
- Both Spring Boot modules compile and test.
- Commit occurs only after verification passes.

Show the resulting branch and `git show --stat`. If GitHub is configured, run the CLI with `--open-pr` and open the generated PR.

## 5. Show the second path — 25 seconds

Use a fresh checkout with `samples/prisma-child-report.json`. Analyze it and show that the agent selects `payments-api/pom.xml` because this version is owned directly by the child.

## 6. Close — 10 seconds

“The MVP proves safe parent and child remediation. Renovate becomes the production update engine, while this platform supplies scanner adapters, policy, validation evidence, shared-BOM orchestration, and auditability across thousands of repositories.”

## Backup if network access fails

Run **Analyze**, which requires no external network. Show the previously verified unit/build results and the deterministic PR body. The Maven Wrapper and GitHub Actions workflow allow the full validation to run when connectivity returns.
