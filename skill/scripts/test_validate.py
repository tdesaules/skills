"""Run with the same PyYAML environment as validate.py: python -m unittest discover -s skill/scripts."""

from pathlib import Path
import tempfile
import unittest

from validate import validate


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.skill = Path(self.temp.name) / "example"
        self.skill.mkdir()

    def check(self, frontmatter, body="Perform the requested task.\n"):
        (self.skill / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        return validate(self.skill)

    def test_valid_optional_fields_and_colons(self):
        result = self.check('name: example\ndescription: >-\n  Use for testing: YAML and links.\nmetadata:\n  version: "1"\nallowed-tools: Read')
        self.assertFalse(result["errors"])

    def test_duplicate_and_malformed_yaml(self):
        for source in ('name: example\nname: other', 'name: [unterminated'):
            with self.subTest(source=source):
                self.assertTrue(self.check(source)["errors"])

    def test_limits_types_and_name(self):
        for source in (
            'name: wrong\ndescription: test',
            'name: example\ndescription: "' + 'x' * 1025 + '"',
            'name: example\ndescription: "   "',
            'name: example\ndescription: test\nmetadata:\n  version: 1',
            'name: example\ndescription: test\ncompatibility: []',
        ):
            with self.subTest(source=source[:80]):
                self.assertTrue(self.check(source)["errors"])

    def test_links_missing_escape_and_valid(self):
        header = 'name: example\ndescription: test'
        for body in ('[missing](references/no.md)', '[escape](../other.md)'):
            self.assertTrue(self.check(header, body)["errors"])
        (self.skill / "reference.md").write_text("Instructions", encoding="utf-8")
        self.assertFalse(self.check(header, '[local](reference.md) [web](https://example.org)')["errors"])

    def test_code_example_links_are_not_dependencies(self):
        self.assertFalse(self.check('name: example\ndescription: test', 'Example:\n```md\n[placeholder](missing.md)\n```\n')["errors"])

    def test_missing_and_invalid_utf8(self):
        self.assertTrue(validate(self.skill)["errors"])
        (self.skill / "SKILL.md").write_bytes(b"\xff")
        self.assertTrue(validate(self.skill)["errors"])


if __name__ == "__main__":
    unittest.main()
