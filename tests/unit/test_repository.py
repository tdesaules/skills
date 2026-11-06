import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_repository", ROOT / ".github/scripts/check_repository.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class RepositoryChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "example"
        self.skill.mkdir()
        self.path = self.skill / "evals.json"
        self.data = {
            "skill_name": "example",
            "evals": [{"id": 1, "prompt": "Review fixture", "expected_output": "Report its defect"}],
            "trigger_queries": [{"query": "Review fixture", "should_trigger": True}],
        }

    def evaluate(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")
        return checks.evaluation_errors(self.path, self.skill)

    def test_valid_evaluations(self):
        self.assertEqual(self.evaluate(), [])

    def test_json_layout_without_forced_reflow(self):
        self.path.write_text('{"compact": true}\n', encoding="utf-8")
        self.assertEqual(checks.json_format_errors(self.path), [])
        self.path.write_text('{"compact": true} ', encoding="utf-8")
        self.assertEqual(len(checks.json_format_errors(self.path)), 2)

    def test_duplicate_ids_and_invalid_boolean(self):
        self.data["evals"].append(self.data["evals"][0].copy())
        self.data["trigger_queries"][0]["should_trigger"] = "false"
        errors = self.evaluate()
        self.assertTrue(any("IDs" in e for e in errors))
        self.assertTrue(any("boolean" in e for e in errors))

    def test_invalid_json_duplicate_key_and_missing_file(self):
        for content in ('{"skill_name":', '{"skill_name":"example","skill_name":"other"}'):
            self.path.write_text(content, encoding="utf-8")
            self.assertTrue(checks.evaluation_errors(self.path, self.skill))
        self.data["evals"][0]["files"] = ["missing.txt"]
        self.assertTrue(self.evaluate())

    def test_fixture_cannot_escape_skill(self):
        (self.root / "outside.txt").write_text("fixture", encoding="utf-8")
        self.data["evals"][0]["files"] = ["../outside.txt"]
        self.assertTrue(self.evaluate())

    def test_reference_links_and_code_examples(self):
        document = self.root / "README.md"
        document.write_text(
            "[guide][ref]\n\n[ref]: missing.md\n\n```md\n[example](not-real.md)\n```\n",
            encoding="utf-8",
        )
        self.assertEqual(checks.local_link_errors(document, self.root), ["missing local link: missing.md"])
        (self.root / "missing.md").write_text("Exists", encoding="utf-8")
        self.assertEqual(checks.local_link_errors(document, self.root), [])

    def test_percent_encoded_paths_and_external_urls(self):
        (self.root / "a b.md").write_text("Exists", encoding="utf-8")
        document = self.root / "README.md"
        document.write_text("[local](a%20b.md) [web](https://example.com) [escape](../outside.md)", encoding="utf-8")
        self.assertEqual(checks.local_link_errors(document, self.root), ["link leaves repository: ../outside.md"])
