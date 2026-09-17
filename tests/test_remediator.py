import json
from pathlib import Path
import shutil
import tempfile
import unittest

import remediator


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT.parent / "vulnerable-java-platform"


class RemediatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repository = Path(self.temp.name) / "target"
        shutil.copytree(TARGET, self.repository)

    def tearDown(self):
        self.temp.cleanup()

    def test_parent_managed_dependency_is_traced_to_root_property(self):
        report = ROOT / "samples" / "nexus-parent-report.json"
        scanner, plans = remediator.analyze(report, self.repository)
        self.assertEqual("NEXUS", scanner)
        self.assertEqual("parent", plans[0].owner)
        self.assertEqual(self.repository / "pom.xml", plans[0].file)
        remediator.apply_change(plans[0])
        self.assertIn("<commons-compress.version>1.26.2</commons-compress.version>",
                      plans[0].file.read_text(encoding="utf-8"))

    def test_child_override_is_changed_without_touching_parent(self):
        report = ROOT / "samples" / "prisma-child-report.json"
        parent_before = (self.repository / "pom.xml").read_text(encoding="utf-8")
        scanner, plans = remediator.analyze(report, self.repository)
        self.assertEqual("PRISMA", scanner)
        self.assertEqual("child", plans[0].owner)
        remediator.apply_change(plans[0])
        self.assertIn("<version>1.26.2</version>",
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
            "package": "org.apache.commons:commons-compress",
            "currentVersion": "0.0.1", "fixedVersion": "1.26.2",
            "module": "orders-api"
        }]}), encoding="utf-8")
        with self.assertRaisesRegex(remediator.RemediationError, "Stale report"):
            remediator.analyze(report, self.repository)


if __name__ == "__main__":
    unittest.main()
