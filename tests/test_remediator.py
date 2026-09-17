import json
import os
from pathlib import Path
import tempfile
import unittest

import remediator


ROOT = Path(__file__).resolve().parents[1]
class RemediatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repository = Path(self.temp.name) / "target"
        (self.repository / "orders-api").mkdir(parents=True)
        (self.repository / "payments-api").mkdir(parents=True)
        (self.repository / "pom.xml").write_text("""<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <properties><log4j.version>2.14.1</log4j.version></properties>
  <dependencyManagement><dependencies><dependency>
    <groupId>org.apache.logging.log4j</groupId><artifactId>log4j-core</artifactId>
    <version>${log4j.version}</version>
  </dependency></dependencies></dependencyManagement>
</project>""", encoding="utf-8")
        (self.repository / "orders-api" / "pom.xml").write_text("""<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion><dependencies><dependency>
    <groupId>org.apache.logging.log4j</groupId><artifactId>log4j-core</artifactId>
  </dependency></dependencies>
</project>""", encoding="utf-8")
        (self.repository / "payments-api" / "pom.xml").write_text("""<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion><dependencies><dependency>
    <groupId>org.apache.commons</groupId><artifactId>commons-compress</artifactId>
    <version>1.25.0</version>
  </dependency></dependencies>
</project>""", encoding="utf-8")
        (self.repository / "mvnw.cmd").write_text("@echo off\r\n", encoding="utf-8")
        (self.repository / "mvnw").write_text("#!/bin/sh\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_parent_managed_dependency_is_traced_to_root_property(self):
        report = ROOT / "samples" / "nexus-parent-report.json"
        scanner, plans = remediator.analyze(report, self.repository)
        self.assertEqual("NEXUS", scanner)
        self.assertEqual("parent", plans[0].owner)
        self.assertEqual(self.repository / "pom.xml", plans[0].file)
        remediator.apply_change(plans[0])
        self.assertIn("<log4j.version>2.17.1</log4j.version>",
                      plans[0].file.read_text(encoding="utf-8"))

    def test_child_override_is_changed_without_touching_parent(self):
        report = ROOT / "samples" / "prisma-child-report.json"
        parent_before = (self.repository / "pom.xml").read_text(encoding="utf-8")
        scanner, plans = remediator.analyze(report, self.repository)
        self.assertEqual("PRISMA", scanner)
        self.assertEqual("child", plans[0].owner)
        remediator.apply_change(plans[0])
        self.assertIn("<version>1.26.0</version>",
                      plans[0].file.read_text(encoding="utf-8"))
        self.assertEqual(parent_before, (self.repository / "pom.xml").read_text(encoding="utf-8"))

    def test_medium_findings_are_not_selected(self):
        report = Path(self.temp.name) / "medium.json"
        report.write_text(json.dumps({"scanner": "TEST", "findings": [{
            "id": "CVE-TEST", "severity": "MEDIUM",
            "package": "org.apache.commons:commons-compress",
            "currentVersion": "1.26.0", "fixedVersion": "1.26.2"
        }]}), encoding="utf-8")
        with self.assertRaisesRegex(remediator.RemediationError, "no Critical or High"):
            remediator.analyze(report, self.repository)

    def test_stale_report_is_rejected(self):
        report = Path(self.temp.name) / "stale.json"
        report.write_text(json.dumps({"scanner": "TEST", "findings": [{
            "id": "CVE-STALE", "severity": "HIGH",
            "package": "org.apache.logging.log4j:log4j-core",
            "currentVersion": "0.0.1", "fixedVersion": "2.17.1",
            "module": "orders-api"
        }]}), encoding="utf-8")
        with self.assertRaisesRegex(remediator.RemediationError, "Stale report"):
            remediator.analyze(report, self.repository)

    def test_validation_command_is_platform_compatible(self):
        command = remediator.validation_command(self.repository)
        if os.name == "nt":
            self.assertIn("cmd", Path(command[0]).stem.lower())
            self.assertIn("/c", command)
            self.assertTrue(any(part.endswith("mvnw.cmd") for part in command))
        else:
            self.assertTrue(command[0].endswith("mvnw"))


if __name__ == "__main__":
    unittest.main()
