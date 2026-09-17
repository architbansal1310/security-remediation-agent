#!/usr/bin/env python3
"""Automated Security Vulnerability Remediation Agent demo.

Uses only the Python standard library. Version selection remains deterministic;
the explanation generator is deliberately isolated so an LLM can be added later.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


ALLOWED_SEVERITIES = {"CRITICAL", "HIGH"}
MAVEN_NS = {"m": "http://maven.apache.org/POM/4.0.0"}


class RemediationError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Finding:
    identifier: str
    severity: str
    package: str
    current_version: str
    fixed_version: str
    module: str | None = None
    description: str = ""
    advisory_url: str = ""

    @property
    def coordinates(self) -> tuple[str, str]:
        parts = self.package.split(":", 1)
        if len(parts) != 2 or not all(parts):
            raise RemediationError(f"Invalid Maven package coordinates: {self.package!r}")
        return parts[0], parts[1]


@dataclasses.dataclass(frozen=True)
class ChangePlan:
    finding: Finding
    owner: str
    file: Path
    old_version: str
    new_version: str
    property_name: str | None = None

    def public(self, repository: Path) -> dict[str, Any]:
        return {
            "findingId": self.finding.identifier,
            "severity": self.finding.severity,
            "package": self.finding.package,
            "module": self.finding.module,
            "owner": self.owner,
            "file": str(self.file.relative_to(repository)),
            "currentVersion": self.old_version,
            "fixedVersion": self.new_version,
        }


def load_findings(report_path: Path) -> tuple[str, list[Finding]]:
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RemediationError(f"Cannot read scanner report: {exc}") from exc
    scanner = str(payload.get("scanner", "UNKNOWN")).upper()
    raw_findings = payload.get("findings")
    if not isinstance(raw_findings, list):
        raise RemediationError("Report must contain a 'findings' array")
    findings: list[Finding] = []
    required = ("id", "severity", "package", "currentVersion", "fixedVersion")
    for index, raw in enumerate(raw_findings):
        if not isinstance(raw, dict):
            raise RemediationError(f"Finding {index} must be an object")
        missing = [name for name in required if not raw.get(name)]
        if missing:
            raise RemediationError(f"Finding {index} is missing: {', '.join(missing)}")
        severity = str(raw["severity"]).upper()
        if severity not in ALLOWED_SEVERITIES:
            continue
        findings.append(Finding(
            identifier=str(raw["id"]), severity=severity,
            package=str(raw["package"]),
            current_version=str(raw["currentVersion"]),
            fixed_version=str(raw["fixedVersion"]),
            module=str(raw["module"]) if raw.get("module") else None,
            description=str(raw.get("description", "")),
            advisory_url=str(raw.get("advisoryUrl", "")),
        ))
    return scanner, findings


def parse_pom(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise RemediationError(f"Cannot parse {path}: {exc}") from exc


def dependency_version(root: ET.Element, group_id: str, artifact_id: str,
                       managed: bool = False) -> str | None:
    prefix = "m:dependencyManagement/m:dependencies" if managed else "m:dependencies"
    dependencies = root.find(prefix, MAVEN_NS)
    if dependencies is None:
        return None
    for dep in dependencies.findall("m:dependency", MAVEN_NS):
        group = dep.findtext("m:groupId", namespaces=MAVEN_NS)
        artifact = dep.findtext("m:artifactId", namespaces=MAVEN_NS)
        if group == group_id and artifact == artifact_id:
            return dep.findtext("m:version", namespaces=MAVEN_NS)
    return None


def locate_change(repository: Path, finding: Finding) -> ChangePlan:
    group_id, artifact_id = finding.coordinates
    if finding.module:
        candidates = [repository / finding.module / "pom.xml"]
    else:
        candidates = sorted(repository.glob("*/pom.xml")) + [repository / "pom.xml"]

    declaring_pom: Path | None = None
    declared_version: str | None = None
    for pom in candidates:
        if not pom.is_file():
            continue
        value = dependency_version(parse_pom(pom), group_id, artifact_id, managed=False)
        if value is not None or _declares_without_version(pom, group_id, artifact_id):
            declaring_pom, declared_version = pom, value
            break
    if declaring_pom is None:
        raise RemediationError(
            f"{finding.package} is not directly declared in module {finding.module or '<any>'}")

    if declared_version:
        old = _resolve_version(repository / "pom.xml", declared_version)
        _verify_report_version(finding, old)
        return ChangePlan(finding, "child", declaring_pom, old,
                          finding.fixed_version,
                          _property_reference(declared_version))

    root_pom = repository / "pom.xml"
    managed_version = dependency_version(parse_pom(root_pom), group_id, artifact_id, managed=True)
    if not managed_version:
        raise RemediationError(f"No managed version found for {finding.package}")
    property_name = _property_reference(managed_version)
    old = _resolve_version(root_pom, managed_version)
    _verify_report_version(finding, old)
    return ChangePlan(finding, "parent", root_pom, old,
                      finding.fixed_version, property_name)


def _declares_without_version(pom: Path, group_id: str, artifact_id: str) -> bool:
    root = parse_pom(pom)
    dependencies = root.find("m:dependencies", MAVEN_NS)
    if dependencies is None:
        return False
    return any(
        dep.findtext("m:groupId", namespaces=MAVEN_NS) == group_id
        and dep.findtext("m:artifactId", namespaces=MAVEN_NS) == artifact_id
        for dep in dependencies.findall("m:dependency", MAVEN_NS)
    )


def _property_reference(value: str) -> str | None:
    match = re.fullmatch(r"\$\{([^}]+)}", value.strip())
    return match.group(1) if match else None


def _verify_report_version(finding: Finding, actual_version: str) -> None:
    if actual_version != finding.current_version:
        raise RemediationError(
            f"Stale report for {finding.package}: report says {finding.current_version}, "
            f"but the POM currently resolves to {actual_version}")


def _resolve_version(root_pom: Path, value: str) -> str:
    property_name = _property_reference(value)
    if not property_name:
        return value.strip()
    root = parse_pom(root_pom)
    properties = root.find("m:properties", MAVEN_NS)
    if properties is None:
        raise RemediationError(f"Property {property_name} is not defined")
    for child in properties:
        if child.tag.rsplit("}", 1)[-1] == property_name and child.text:
            return child.text.strip()
    raise RemediationError(f"Property {property_name} is not defined")


def apply_change(plan: ChangePlan) -> None:
    text = plan.file.read_text(encoding="utf-8")
    if plan.property_name:
        pattern = re.compile(
            rf"(<{re.escape(plan.property_name)}>\s*){re.escape(plan.old_version)}(\s*</{re.escape(plan.property_name)}>)")
        updated, count = pattern.subn(rf"\g<1>{plan.new_version}\g<2>", text, count=1)
    else:
        group_id, artifact_id = plan.finding.coordinates
        pattern = re.compile(
            rf"(<dependency>\s*.*?<groupId>\s*{re.escape(group_id)}\s*</groupId>\s*"
            rf".*?<artifactId>\s*{re.escape(artifact_id)}\s*</artifactId>\s*"
            rf".*?<version>\s*){re.escape(plan.old_version)}(\s*</version>.*?</dependency>)",
            re.DOTALL,
        )
        updated, count = pattern.subn(rf"\g<1>{plan.new_version}\g<2>", text, count=1)
    if count != 1:
        raise RemediationError(
            f"Expected one safe replacement in {plan.file}, found {count}")
    plan.file.write_text(updated, encoding="utf-8", newline="")


def analyze(report_path: Path, repository: Path) -> tuple[str, list[ChangePlan]]:
    repository = repository.resolve()
    if not (repository / "pom.xml").is_file():
        raise RemediationError(f"No root pom.xml found in {repository}")
    scanner, findings = load_findings(report_path.resolve())
    if not findings:
        raise RemediationError("The report contains no Critical or High findings")
    return scanner, [locate_change(repository, finding) for finding in findings]


def git(repository: Path, *args: str, capture: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repository, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "git command failed").strip()
        raise RemediationError(detail)
    return (result.stdout or "").strip()


def ensure_clean_repository(repository: Path) -> None:
    if git(repository, "rev-parse", "--is-inside-work-tree") != "true":
        raise RemediationError(f"{repository} is not a Git repository")
    dirty = git(repository, "status", "--porcelain")
    if dirty:
        raise RemediationError("Target repository has uncommitted changes; commit or stash them first")


def validation_command(repository: Path) -> list[str]:
    override = os.environ.get("MAVEN_EXECUTABLE")
    if override:
        return _maven_command(Path(override))
    wrapper = repository / ("mvnw.cmd" if os.name == "nt" else "mvnw")
    if wrapper.is_file():
        return _maven_command(wrapper)
    executable = shutil.which("mvn")
    if executable:
        return _maven_command(Path(executable))
    raise RemediationError("Maven is unavailable. Install Maven or set MAVEN_EXECUTABLE")


def _maven_command(executable: Path) -> list[str]:
    arguments = [str(executable), "--batch-mode", "--no-transfer-progress", "verify"]
    if os.name == "nt" and executable.suffix.lower() in {".cmd", ".bat"}:
        command_interpreter = os.environ.get("COMSPEC") or shutil.which("cmd.exe")
        if not command_interpreter:
            raise RemediationError("Windows command interpreter cmd.exe is unavailable")
        return [command_interpreter, "/d", "/c", *arguments]
    return arguments


def validate(repository: Path) -> dict[str, Any]:
    command = validation_command(repository)
    result = subprocess.run(command, cwd=repository, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout or ""
    return {
        "passed": result.returncode == 0,
        "command": command,
        "exitCode": result.returncode,
        "output": output[-12000:],
    }


def generate_pr_body(scanner: str, plans: list[ChangePlan], validation: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| {p.finding.identifier} | {p.finding.severity} | `{p.finding.package}` | "
        f"{p.old_version} | {p.new_version} | {p.owner} |"
        for p in plans
    )
    return f"""## Automated security remediation

This human-reviewed change was generated from a **{scanner}**-format security report.

| Finding | Severity | Dependency | From | To | Version owner |
|---|---|---|---|---|---|
{rows}

### Decision

The scanner-provided lowest fixed version was selected. The agent traced each dependency to its owning Maven POM and changed only that version declaration. No automatic merge is requested.

### Validation

- Maven verification: **{'PASSED' if validation['passed'] else 'FAILED'}**
- Command: `{' '.join(validation['command'])}`

### Required review

- Confirm application behavior and release notes.
- Confirm the security finding is cleared by the repository scanner.
- Merge only after required GitHub checks and human approval pass.

_Generated by the Automated Security Vulnerability Remediation Agent._
"""


def github_location(repository: Path) -> tuple[str, str]:
    remote = git(repository, "remote", "get-url", "origin")
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    if not match:
        raise RemediationError("The origin remote is not a GitHub repository")
    return match.group(1), match.group(2)


def open_github_pr(repository: Path, branch: str, base: str,
                   title: str, body: str) -> str:
    token = _github_token()
    if not token:
        raise RemediationError(
            "GitHub authentication is required. Run 'git credential-manager github login' "
            "or set GITHUB_TOKEN for the current terminal")
    owner, repo = github_location(repository)
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        data=json.dumps({"title": title, "head": branch, "base": base, "body": body}).encode(),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "security-remediation-agent-demo",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
            return str(payload["html_url"])
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RemediationError(f"GitHub API returned {exc.code}: {detail}") from exc


def _github_token() -> str | None:
    """Read a token from the environment or Git Credential Manager without logging it."""
    if token := os.environ.get("GITHUB_TOKEN"):
        return token
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("password="):
            return line.removeprefix("password=")
    return None


def remediate(report_path: Path, repository: Path, *, skip_validation: bool = False,
              push: bool = False, create_pr: bool = False, base: str = "main") -> dict[str, Any]:
    repository = repository.resolve()
    scanner, plans = analyze(report_path, repository)
    ensure_clean_repository(repository)
    if not skip_validation:
        validation_command(repository)  # Fail before branching if Maven is unavailable.
    slug = re.sub(r"[^a-z0-9]+", "-", plans[0].finding.identifier.lower()).strip("-")
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    branch = f"remediation/{slug}-{stamp}"
    git(repository, "switch", "-c", branch)
    for plan in plans:
        apply_change(plan)

    validation = ({"passed": True, "command": ["skipped"], "exitCode": 0, "output": ""}
                  if skip_validation else validate(repository))
    body = generate_pr_body(scanner, plans, validation)
    result: dict[str, Any] = {
        "status": "validated" if validation["passed"] else "validation_failed",
        "scanner": scanner,
        "branch": branch,
        "changes": [plan.public(repository) for plan in plans],
        "validation": validation,
        "pullRequestUrl": None,
        "pullRequestBody": body,
    }
    if not validation["passed"]:
        return result

    git(repository, "add", *sorted({str(p.file.relative_to(repository)) for p in plans}))
    git(repository, "-c", "user.name=Remediation Agent",
        "-c", "user.email=remediation-agent@example.invalid",
        "commit", "-m", f"fix(security): remediate {plans[0].finding.identifier}")
    result["status"] = "committed"
    if push or create_pr:
        git(repository, "push", "--set-upstream", "origin", branch)
        result["status"] = "pushed"
    if create_pr:
        title = f"fix(security): remediate {plans[0].finding.identifier}"
        result["pullRequestUrl"] = open_github_pr(repository, branch, base, title, body)
        result["status"] = "pr_opened"
    return result


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("analyze", "remediate"):
        command = subparsers.add_parser(name)
        command.add_argument("--report", required=True, type=Path)
        command.add_argument("--repo", required=True, type=Path)
        if name == "remediate":
            command.add_argument("--skip-validation", action="store_true")
            command.add_argument("--push", action="store_true")
            command.add_argument("--open-pr", action="store_true")
            command.add_argument("--base", default="main")
    serve = subparsers.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8080, type=int)

    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            scanner, plans = analyze(args.report, args.repo)
            repo = args.repo.resolve()
            _print_json({"scanner": scanner, "status": "ready",
                         "changes": [plan.public(repo) for plan in plans]})
        elif args.command == "remediate":
            _print_json(remediate(
                args.report, args.repo,
                skip_validation=args.skip_validation,
                push=args.push or args.open_pr,
                create_pr=args.open_pr,
                base=args.base,
            ))
        else:
            from server import serve as start_server
            start_server(args.host, args.port)
        return 0
    except RemediationError as exc:
        _print_json({"status": "error", "message": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
